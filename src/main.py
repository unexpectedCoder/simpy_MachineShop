from typing import Generator
import simpy

from machine import Machine


def main():
    # Setup and start the simulation
    print("*** Machine Shop ***")
    num_machines = 10               # number of machines in the machine shop
    weeks = 4                       # simulation time in weeks
    sim_time = weeks * 7 * 24 * 60  # simulation time in minutes

    # Create an environment and start the setup process
    env = simpy.Environment()
    repairman = simpy.PreemptiveResource(env, capacity=1)
    machines = [Machine(env, f'Machine #{i + 1}', repairman) for i in range(num_machines)]
    env.process(other_job(env, repairman, job_duration=30.))

    # Execute
    env.run(until=sim_time)

    # Analysis/results
    print(f"Machine shop results after {weeks} weeks")
    for machine in machines:
        print(f"{machine.name} made {machine.parts_made} parts")

    return 0


def other_job(env: simpy.Environment, repairman: simpy.PreemptiveResource,
              **kwargs) -> Generator:
    """The repairman's other (unimportant) job."""
    job_duration = kwargs['job_duration'] if 'job_duration' in kwargs else 0.

    while True:
        # Start a new job
        done_in = job_duration
        while done_in:
            # Retry the job until it is done
            # It's priority is lower than that of machine repairs
            with repairman.request(priority=2) as req:
                yield req
                start = env.now
                try:
                    yield env.timeout(done_in)
                    done_in = 0
                except simpy.Interrupt:
                    done_in -= env.now - start


if __name__ == '__main__':
    main()
