# views.py
from django.shortcuts import render, redirect
from django.conf import settings
from django.http import JsonResponse,HttpResponse
from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from fyers_apiv3 import fyersModel
from .services import FyersTokenService

class FyersAuthView(View):
    """
    View to handle Fyers authentication for administrators
    """
    
    def get(self, request):
        """Generate and return Fyers auth URL or show auth form"""
        client_id = settings.FYERS_CLIENT_ID
        redirect_uri = settings.FYERS_REDIRECT_URI
        secret_key = settings.FYERS_SECRET_KEY
        response_type = "code" 
        
        session = fyersModel.SessionModel(
                        client_id=client_id,
                        secret_key=secret_key,
                        redirect_uri=redirect_uri,
                        response_type=response_type
                    )

        response = session.generate_authcode()

        print("respinse",response)

        context = {
            'auth_url': response
        }
        return render(request, 'fyers_auth.html', context)


class FyersCallbackView(View):
    """
    View to handle Fyers callback after authentication
    """
    
    def get(self, request):
        """Process auth code from Fyers callback"""
        auth_code = request.GET.get('auth_code')

        print("i am called in this function",auth_code)
        # client_id = settings.FYERS_CLIENT_ID
        # redirect_uri = settings.FYERS_REDIRECT_URI
        # secret_key = settings.FYERS_SECRET_KEY
        # response_type = "code" 
        # grant_type = "authorization_code" 
        
        # session = fyersModel.SessionModel(
        #                 client_id=client_id,
        #                 secret_key=secret_key,
        #                 redirect_uri=redirect_uri,
        #                 response_type=response_type,
        #                 grant_type=grant_type
        #             )

        # session.set_token(auth_code)

        # response = session.generate_token()

        # print("token response",response)
                
        if not auth_code:
            return render(request, 'fyers_callback.html', {'success': False, 'message': 'No auth code provided'})
        
        access_token = FyersTokenService.initialize_token(auth_code)
        
        if access_token:
            return render(request, 'fyers_callback.html', {'success': True, 'message': 'Authentication successful'})
        else:
            return render(request, 'fyers_callback.html', {'success': False, 'message': 'Authentication failed'})


class StockPriceAPIView(APIView):
    """
    API view to get stock prices
    """
    
    def get(self, request, symbol=None):
        """Get stock price data"""
        # Get symbols from query params
        symbols = request.query_params.getlist('symbol')
        
        # If no symbols provided in query params but symbol in URL, use that
        if not symbols and symbol:
            symbols = [symbol]
        
        if not symbols:
            return Response({"error": "No symbols provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Format symbols for Fyers API
        formatted_symbols = []
        for sym in symbols:
            if ':' not in sym:
                # Default format if exchange not specified
                sym = f"NSE:{sym}-EQ"
            formatted_symbols.append(sym)
        
        # Get a valid access token
        access_token = FyersTokenService.get_access_token()

        print("at",access_token)
        
        if not access_token:
            return Response({
                "error": "API token is invalid or expired. Please reauthorize.",
                "auth_required": True
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Use Fyers API to get data
        try:
            fyers = fyersModel.FyersModel(
                client_id=settings.FYERS_CLIENT_ID,
                is_async=False,
                token=access_token
            )
            
            # Example of a quotes request
            data = {
                "symbol": formatted_symbols,
                "ohlcv_flag": 1
            }
            
            print("data",data)
            response = fyers.quotes(data)

            print("res",response)
            
            if response.get('s') == 'ok':
                return Response(response.get('d', {}))
            else:
                # If the error is related to invalid token, notify caller
                error_msg = response.get('message', '')
                if 'Invalid token' in error_msg or 'Unauthorized' in error_msg:
                    return Response({
                        "error": "API token is invalid. Please reauthorize.",
                        "auth_required": True
                    }, status=status.HTTP_401_UNAUTHORIZED)
                
                return Response({"error": error_msg}, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def home(request):
    print("hgello")
    return HttpResponse("Hello, World!")