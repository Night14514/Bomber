"""
Universal Request Handler for SMS Bomber
Supports all HTTP request formats encountered in attack_urls.py
"""
import aiohttp
import json
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlencode


class RequestHandler:
    """Universal handler for different HTTP request formats."""
    
    @staticmethod
    def determine_request_type(service: Dict[str, Any]) -> Dict[str, Any]:
        """Determine the request type and format."""
        method = service.get('method', 'POST').upper()
        has_data = 'data' in service
        has_json = 'json' in service
        has_params = 'params' in service
        has_cookies = 'cookies' in service
        
        # Determine data type
        data_type = None
        if has_data:
            data = service['data']
            if isinstance(data, dict):
                data_type = 'dict'
            elif isinstance(data, str):
                data_type = 'string'
            elif isinstance(data, (int, float, bool)):
                data_type = 'primitive'
        
        # Determine content type from headers
        content_type = None
        if 'headers' in service:
            headers = service['headers']
            if isinstance(headers, dict):
                content_type = headers.get('Content-Type') or headers.get('content-type')
        
        return {
            'method': method,
            'has_data': has_data,
            'has_json': has_json,
            'has_params': has_params,
            'has_cookies': has_cookies,
            'data_type': data_type,
            'content_type': content_type
        }
    
    @staticmethod
    def prepare_request_data(service: Dict[str, Any]) -> Tuple[Optional[Dict], Optional[Dict], Optional[str]]:
        """
        Prepare request data for aiohttp.
        Returns (data, json, content_type) tuple.
        """
        req_type = RequestHandler.determine_request_type(service)
        
        data = None
        json_data = None
        content_type = None
        
        # Handle JSON payload
        if req_type['has_json']:
            json_data = service['json']
            content_type = 'application/json'
        
        # Handle data payload
        elif req_type['has_data']:
            data_value = service['data']
            content_type = req_type['content_type']
            
            if req_type['data_type'] == 'dict':
                # Check if it should be form-encoded or multipart
                if content_type and 'multipart/form-data' in content_type:
                    # For multipart, aiohttp handles it automatically with dict
                    data = data_value
                elif content_type and 'application/x-www-form-urlencoded' in content_type:
                    # Form-encoded
                    data = data_value
                else:
                    # Default to form-encoded for dict
                    data = data_value
            
            elif req_type['data_type'] == 'string':
                # Raw string body
                data = data_value
            
            elif req_type['data_type'] == 'primitive':
                # Primitive type - convert to string
                data = str(data_value)
        
        return data, json_data, content_type
    
    @staticmethod
    def prepare_headers(service: Dict[str, Any], content_type: Optional[str]) -> Dict[str, str]:
        """Prepare headers for the request."""
        headers = {}
        
        if 'headers' in service:
            service_headers = service['headers']
            if isinstance(service_headers, dict):
                headers = service_headers.copy()
        
        # Ensure Content-Type is set if we have a specific one
        if content_type and 'Content-Type' not in headers and 'content-type' not in headers:
            headers['Content-Type'] = content_type
        
        return headers
    
    @staticmethod
    def prepare_params(service: Dict[str, Any]) -> Optional[Dict]:
        """Prepare query parameters."""
        if 'params' in service:
            params = service['params']
            if isinstance(params, dict):
                return params
        return None
    
    @staticmethod
    def prepare_cookies(service: Dict[str, Any]) -> Optional[Dict]:
        """Prepare cookies."""
        if 'cookies' in service:
            cookies = service['cookies']
            if isinstance(cookies, dict):
                return cookies
        return None
    
    @staticmethod
    async def send_request(session: aiohttp.ClientSession, service: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send HTTP request using the appropriate format.
        
        Returns:
            Dict with keys: status, success, error, response_text, status_code
        """
        req_type = RequestHandler.determine_request_type(service)
        
        try:
            # Prepare request components
            data, json_data, content_type = RequestHandler.prepare_request_data(service)
            headers = RequestHandler.prepare_headers(service, content_type)
            params = RequestHandler.prepare_params(service)
            cookies = RequestHandler.prepare_cookies(service)
            
            url = service['url']
            method = req_type['method']
            
            # Make the request
            async with session.request(
                method=method,
                url=url,
                headers=headers,
                data=data,
                json=json_data,
                params=params,
                cookies=cookies,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                status_code = response.status
                response_text = await response.text()
                
                # Determine success based on status code
                success = 200 <= status_code < 300
                
                return {
                    'status': 'success',
                    'success': success,
                    'error': None,
                    'response_text': response_text[:500],  # Limit response text
                    'status_code': status_code,
                    'request_type': req_type
                }
                
        except aiohttp.ClientError as e:
            return {
                'status': 'error',
                'success': False,
                'error': f'ClientError: {str(e)}',
                'response_text': None,
                'status_code': None,
                'request_type': req_type
            }
        except Exception as e:
            return {
                'status': 'error',
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'response_text': None,
                'status_code': None,
                'request_type': req_type
            }


class RequestTypeClassifier:
    """Classifier for request types to help with debugging and analysis."""
    
    @staticmethod
    def classify(service: Dict[str, Any]) -> str:
        """Classify service into a human-readable type."""
        req_type = RequestHandler.determine_request_type(service)
        
        parts = [req_type['method']]
        
        if req_type['has_json']:
            parts.append('JSON')
        elif req_type['has_data']:
            if req_type['data_type'] == 'dict':
                parts.append('FORM_DATA')
            elif req_type['data_type'] == 'string':
                parts.append('RAW_BODY')
            else:
                parts.append('DATA')
        
        if req_type['has_params']:
            parts.append('PARAMS')
        
        if req_type['has_cookies']:
            parts.append('COOKIES')
        
        return '_'.join(parts)
