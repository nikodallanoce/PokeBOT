import asyncio

from src.utilities.RandomSearch import RandomSearch


if __name__ == '__main__':
    search = RandomSearch(n_matches=1000)
    run = asyncio.new_event_loop()
    run.run_until_complete(search.compute(num_config=100))