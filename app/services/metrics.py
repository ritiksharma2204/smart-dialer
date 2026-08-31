from dataclasses import dataclass


@dataclass
class DialerMetrics:
    total_calls: int
    queued_calls: int
    reserved_calls: int
    initiated_calls: int
    ringing_calls: int
    answered_calls: int
    connected_calls: int
    completed_calls: int
    failed_calls: int
    cancelled_calls: int

    @property
    def answer_rate(self) -> float:
        attempted = (
            self.initiated_calls
            + self.ringing_calls
            + self.answered_calls
            + self.connected_calls
            + self.completed_calls
            + self.failed_calls
            + self.cancelled_calls
        )

        if attempted == 0:
            return 0.0

        successful = (
            self.answered_calls
            + self.connected_calls
            + self.completed_calls
        )

        return successful / attempted
