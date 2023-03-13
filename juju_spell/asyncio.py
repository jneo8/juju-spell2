import typing as t
import asyncio


def run_async(
    funcs: t.List[t.Union[t.Coroutine[t.Any, t.Any, t.Any], t.Generator[t.Any, None, t.Any]]]
) -> t.Any:
    loop = asyncio.get_event_loop()
    tasks = []
    for func in funcs:
        task: asyncio.Task = loop.create_task(func)
        tasks.append(task)
    loop.run_until_complete(asyncio.gather(*tasks))
    return [task.result() for task in tasks]
