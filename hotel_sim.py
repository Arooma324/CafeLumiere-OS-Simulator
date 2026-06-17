from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple


#  Customer = Process, Table = Shared Resource, Semaphore = sync controller

class CustomerState(Enum):
    NEW       = "New"
    WAITING   = "Waiting"
    SEATED    = "Seated (Running)"
    COMPLETED = "Completed"
    REJECTED  = "Rejected"


class ReservationType(Enum):
    NORMAL = "Normal"
    VIP    = "VIP"
    URGENT = "Urgent"


@dataclass
class Customer:
    customer_id:      int
    name:             str
    num_guests:       int
    arrival_time:     str
    dining_duration:  int
    reservation_type: ReservationType = ReservationType.NORMAL
    state:            CustomerState   = CustomerState.NEW
    assigned_table:   object          = None
    waiting_time:     float           = 0.0
    arrival_order:    int             = 0

    @property
    def priority(self) -> int:
        return {ReservationType.URGENT: 1,
                ReservationType.VIP:    2,
                ReservationType.NORMAL: 3}[self.reservation_type]

    @property
    def priority_label(self) -> str:
        return self.reservation_type.value


@dataclass
class Table:
    table_id:       int
    capacity:       int
    is_occupied:    bool     = False
    occupied_by:    Customer = None
    time_remaining: int      = 0

    @property
    def status_label(self):
        return f"Occupied – {self.occupied_by.name}" if self.is_occupied else "Available"


class CountingSemaphore:
    """
    Counting Semaphore — controls number of available tables.
    P() = acquire (wait),  V() = release (signal)
    """
    def __init__(self, total: int):
        self.total    = total
        self.value    = total
        self._history = []

    def wait(self, customer_name: str) -> bool:
        if self.value > 0:
            self.value -= 1
            self._history.append(f"P()  [{customer_name}]  →  S = {self.value}")
            return True
        self._history.append(f"P()  [{customer_name}]  BLOCKED  →  S = {self.value}")
        return False

    def signal(self, table_id) -> None:
        self.value += 1
        self._history.append(f"V()  [Table {table_id} released]  →  S = {self.value}")

    @property
    def occupied(self):
        return self.total - self.value

    def last_op(self):
        return self._history[-1] if self._history else "—"



class Scheduler:
    def __init__(self, tables: List[Table], semaphore: CountingSemaphore):
        self.tables         = tables
        self.semaphore      = semaphore
        self.waiting_queue  = []
        self.served         = []
        self.rejected       = []
        self.algorithm      = "FCFS"
        self._order_counter = 0
        self.log            = []
        self.seat_history   = []   # [(customer, table_id, duration, priority_label)]

    def _best_table(self, num_guests: int) -> Optional[Table]:
        candidates = [t for t in self.tables
                      if not t.is_occupied and t.capacity >= num_guests]
        return min(candidates, key=lambda t: t.capacity) if candidates else None

    def _sort_queue(self):
        if self.algorithm == "FCFS":
            self.waiting_queue.sort(key=lambda c: c.arrival_order)
        else:
            self.waiting_queue.sort(key=lambda c: (c.priority, c.arrival_order))

    def _seat(self, customer: Customer, table: Table):
        table.is_occupied       = True
        table.occupied_by       = customer
        table.time_remaining    = customer.dining_duration
        customer.state          = CustomerState.SEATED
        customer.assigned_table = table
        self.log.append(
            f"✔  {customer.name}  →  Table {table.table_id} "
            f"({table.capacity}-seat)  [{customer.priority_label}]"
        )
        self.seat_history.append({
            "name":     customer.name,
            "table_id": table.table_id,
            "duration": customer.dining_duration,
            "priority": customer.priority_label,
            "order":    customer.arrival_order,
        })

    def add_customer(self, customer: Customer) -> Tuple[bool, str]:
        self._order_counter   += 1
        customer.arrival_order = self._order_counter

        max_cap = max(t.capacity for t in self.tables)
        if customer.num_guests > max_cap:
            customer.state = CustomerState.REJECTED
            self.rejected.append(customer)
            msg = (f"✘  {customer.name} REJECTED — party of {customer.num_guests} "
                   f"exceeds max capacity ({max_cap} seats).")
            self.log.append(msg)
            return False, msg

        acquired = self.semaphore.wait(customer.name)
        if not acquired:
            customer.state = CustomerState.WAITING
            self.waiting_queue.append(customer)
            msg = f"⏳  {customer.name} added to waiting queue (all tables occupied)."
            self.log.append(msg)
            return False, msg

        table = self._best_table(customer.num_guests)
        if table is None:
            self.semaphore.signal(-1)
            customer.state = CustomerState.WAITING
            self.waiting_queue.append(customer)
            msg = (f"⏳  {customer.name} waiting — no table with "
                   f"{customer.num_guests}+ seats free right now.")
            self.log.append(msg)
            return False, msg

        self._seat(customer, table)
        return True, f"✔  {customer.name} seated at Table {table.table_id}."

    def release_table(self, table: Table) -> List[str]:
        messages = []
        if not table.is_occupied:
            return ["Table is already free."]

        customer                = table.occupied_by
        customer.state          = CustomerState.COMPLETED
        customer.assigned_table = None
        table.is_occupied       = False
        table.occupied_by       = None
        table.time_remaining    = 0
        self.served.append(customer)
        self.semaphore.signal(table.table_id)
        messages.append(
            f"🚪  {customer.name} left Table {table.table_id}.  "
            f"S → {self.semaphore.value}"
        )
        self.log.append(messages[-1])

        self._sort_queue()
        for waiting_cust in list(self.waiting_queue):
            t = self._best_table(waiting_cust.num_guests)
            if t:
                self.waiting_queue.remove(waiting_cust)
                self._seat(waiting_cust, t)
                self.semaphore.wait(waiting_cust.name)
                msg = f"✔  {waiting_cust.name} moved from queue → Table {t.table_id}."
                messages.append(msg)
                self.log.append(msg)
                break

        return messages

    def get_stats(self) -> dict:
        return {
            "total_customers":  len(self.served) + len(self.waiting_queue) + len(self.rejected),
            "served":           len(self.served),
            "currently_seated": sum(1 for t in self.tables if t.is_occupied),
            "waiting":          len(self.waiting_queue),
            "rejected":         len(self.rejected),
            "available_tables": self.semaphore.value,
            "occupied_tables":  self.semaphore.occupied,
            "semaphore_value":  self.semaphore.value,
        }
