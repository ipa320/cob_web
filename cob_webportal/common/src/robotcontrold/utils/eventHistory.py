import time

class Callable:
    def __init__(self, anycallable):
        self.__call__ = anycallable

class EventHistory:
	ACTION_STATUS_EVENT=1
	HOST_EVENT = 2
	ACTION_STATE_EVENT=3
	
	_eventData=[]
	
	def actionRun(action, comp):
		EventHistory._eventData.append({'type': EventHistory.ACTION_STATUS_EVENT, 'status':1, 'timestamp': int(time.time()), 'id': action.id, 'comp': comp.id})
	actionRun=Callable(actionRun)

	def actionStopped(action, comp):
		EventHistory._eventData.append({'type': EventHistory.ACTION_STATUS_EVENT, 'status':0, 'timestamp': int(time.time()), 'id': action.id, 'comp': comp.id})
	actionStopped=Callable(actionStopped)
	
	def hostOnline(host):
		EventHistory._eventData.append({'type': EventHistory.HOST_EVENT, 'status':1, 'timestamp': int(time.time()), 'id': host.id})
	hostOnline=Callable(hostOnline)
		
	def hostOffline(host):
		EventHistory._eventData.append({'type': EventHistory.HOST_EVENT, 'status':0, 'timestamp': int(time.time()), 'id':host.id})
	hostOffline=Callable(hostOffline)

	def newState( action, comp, state ):
		EventHistory._eventData.append({'type': EventHistory.ACTION_STATE_EVENT, 'state':state, 'timestamp': int(time.time()), 'id': action.id, 'comp': comp.id})
	newState=Callable(newState)

	def getEventData(timestamp):
		data = []
		for item in reversed(EventHistory._eventData):
			if item['timestamp'] < timestamp:
				break
			data.append(item)
		return data
	getEventData=Callable(getEventData)

	def clear():
		EventHistory._eventData=[]
	clear=Callable(clear)
