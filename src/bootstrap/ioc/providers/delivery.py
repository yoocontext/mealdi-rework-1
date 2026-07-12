from dishka import Provider, Scope, provide

from delivery.common.connections import MessageConnections


class DeliveryProvider(Provider):
    @provide(scope=Scope.APP)
    def message_connections(self) -> MessageConnections:
        return MessageConnections()
