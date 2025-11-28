from urllib.parse import parse_qs
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware

from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

User = get_user_model()

class WebSocketJWTAuthMiddleware(BaseMiddleware):
    """
    Custom middleware to authenticate WebSocket connections using JWT
    """
    
    async def __call__(self, scope, receive, send):
        query_string = scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        token = query_params.get('token', [None])[0]

        if not token:
            scope['user'] = AnonymousUser()
        else:
            try:
                scope['user'] = await self.get_user_from_token(token)
            except Exception as e:
                scope['user'] = AnonymousUser()

        return await super().__call__(scope, receive, send)

    @database_sync_to_async
    def get_user_from_token(self, token_str):
        """
        Get user from token string. This now handles validation and user lookup.
        """
        try:
            access_token = AccessToken(token_str)
            user_id = access_token['user_id']
            
            
            user = User.objects.get(id=user_id)
            return user
        
        except InvalidToken as e:
            return AnonymousUser()
        except TokenError as e:
            return AnonymousUser()
        except User.DoesNotExist:
            return AnonymousUser()
        except Exception as e:
            return AnonymousUser()
