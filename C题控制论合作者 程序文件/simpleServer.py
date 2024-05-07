import asyncio
import websockets
from remotePlayer import player
from player import programmer
from remoteGame import game
import threading


async def handler(websocket):
    if len(players) > 3:
        return
    else:
        play = player(websocket)
        players.append(play)
    print(len(players))
    if len(players) == 3:
        t = threading.Thread(target=startGame)
        t.start()
    while True:
        result = await websocket.recv()
        play.result.put(result)
        play.event.set()


def startGame():
    theGame = game(players=players)
    theGame.start()


async def main():
    async with websockets.serve(handler, "127.0.0.1", 9999):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    global players
    players = [programmer(.2, 1), programmer(.2, 1)]
    global task
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    task = asyncio.get_event_loop().create_task(main())
    print('running')
    loop.run_until_complete(task)
