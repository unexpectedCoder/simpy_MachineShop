from typing import Generator
import random
import simpy


random.seed(42)


class Machine:
    """A machine produces parts and may get broken every now and then.

    If it breaks, it requests a *repairman* and continues the production
    after the it is repaired.

    A machine has a *name* and a number of *parts_made* thus far.
    """

    PT_MEAN = 10.           # avg. processing time in minutes
    PT_SIGMA = 2.           # sigma of processing time
    MTTF = 300.             # mean time to failure in minutes
    BREAK_MEAN = 1 / MTTF   # param. for expovariate distribution
    REPAIR_TIME = 30.       # time it takes to repair a machine in minutes

    def __init__(self, env: simpy.Environment, name: str, repairman: simpy.PreemptiveResource):
        self.env = env
        self.name = name
        self.parts_made = 0
        self.broken = False

        # Start "working" and "break_machine" processes for this machine
        self.process = self.env.process(self.working(repairman))
        self.env.process(self.break_machine())

    def working(self, repairman: simpy.PreemptiveResource) -> Generator:
        """Produce parts as long as the simulation runs.

        While making a part, the machine may break multiple times.
        Request a repairman when this happens.
        """
        while True:
            # Start making a new part
            done_in = self.time_per_part()
            while done_in:
                start = self.env.now
                try:
                    yield self.env.timeout(done_in)
                    done_in = 0
                except simpy.Interrupt:
                    self.broken = True
                    done_in -= self.env.now - start     # How much time left?

                    # Request a repairman. This will preempt its "other_job"
                    with repairman.request(priority=1) as req:
                        yield req
                        yield self.env.timeout(self.REPAIR_TIME)
                    self.broken = False

                # Part is done
                self.parts_made += 1

    def break_machine(self) -> Generator:
        """Break the machine every now and then."""
        while True:
            yield self.env.timeout(self.time_to_failure())
            if not self.broken:
                # Only break the machine if it is currently working
                self.process.interrupt()

    def time_per_part(self) -> float:
        """:return: The actual processing time for a concrete part."""
        return random.normalvariate(self.PT_MEAN, self.PT_SIGMA)

    def time_to_failure(self) -> float:
        """:return: The time until next failure for a machine."""
        return random.expovariate(self.BREAK_MEAN)
