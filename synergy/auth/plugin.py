from synergy.exception import AuthorizationError

class LocalHostAuthorization(object):

    def authorize(self, context):
        server_addr = context.get("SERVER_NAME")
        remote_addr = context.get("REMOTE_ADDR")

        if not server_addr or not remote_addr or server_addr != remote_addr:
            raise AuthorizationError("You are not authorized!")

