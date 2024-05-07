from remoteGame import endgames, colors, actions, action, card
from basePlayer import basePlayer
import json
import asyncio
from queue import Queue

class player(basePlayer):
    def __init__(self, playerSocket):
        basePlayer.__init__(self)
        self.onStart.append(self.onstart)
        self.onGameEnd.append(self.ongameend)
        self.onTurnStart.append(self.onturnstart)
        self.onHintColor.append(self.onhintcolor)
        self.onHintNumber.append(self.onhintnumber)
        self.onPlayerAction.append(self.onplayeraction)
        self.socket = playerSocket
        self.result = Queue()
        self.event = asyncio.Event()

    async def trigger(self, event, load):
        load["event"] = event
        await self.socket.send(json.dumps(load).encode())

    def onstart(self, handStatus):
        handColor = [[c.color.value for c in i] for i in handStatus]
        handNumber = [[c.number for c in i] for i in handStatus]
        asyncio.run(self.trigger("onStart", {"handColor": handColor, "handNumber": handNumber}))

    def ongameend(self, reason, score):
        asyncio.run(self.trigger("onGameEnd", {"reason": reason.value, "score": score}))

    def onturnstart(self, index):
        asyncio.run(self.trigger("onTurnStart", {"index": index}))

    def onhintcolor(self, hintInfo):
        hintColor = [c.color.value for c in hintInfo]
        hintNumber = [c.number for c in hintInfo]
        asyncio.run(self.trigger("onHintColor", {"hintColor": hintColor, "hintNumber": hintNumber}))

    def onhintnumber(self, hintInfo):
        hintColor = [c.color.value for c in hintInfo]
        hintNumber = [c.number for c in hintInfo]
        asyncio.run(self.trigger("onHintNumber", {"hintColor": hintColor, "hintNumber": hintNumber}))

    def onplayeraction(self, index, playerAction, **kwargs):
        load = {"index": index, "actionType": playerAction.actionType.value, "target": playerAction.target}
        if playerAction.actionType == actions.hintColor:
            load['color'] = playerAction.color.value
        elif playerAction.actionType == actions.hintNumber:
            load['number'] = playerAction.number
        for i in kwargs.keys():
            load[i] = [kwargs[i].color.value, kwargs[i].number]
        asyncio.run(self.trigger("onPlayerAction", load))

    def turn(self):
        asyncio.run(self.trigger("turn", {}))
        self.event.wait()
        # unfortunately, the result can hardly, if ever, be awaited inside remotePlayer
        result = json.loads(self.result.get())
        if result['actionType'] == actions.hintColor.value:
            return action(actions(result['actionType']), result['target'], color=colors(result['color']))
        elif result['actionType'] == actions.hintNumber.value:
            return action(actions(result['actionType']), result['target'], number=result['number'])
        return action(actions(result['actionType']), result['target'])
