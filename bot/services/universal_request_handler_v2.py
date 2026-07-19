"""
Universal Request Handler v2 - Advanced HTTP Request Processing
Supports all HTTP methods and data formats encountered in attack_urls.py
"""
import aiohttp
import json
from typing import Dict, Any, Optional, Tuple, Union
from urllib.parse import urlencode


class RequestType:
    """Request type classification."""
    JSON = 'json'
    FORM_DATA = 'form_data'
    FORM_URLENCODED = 'form_urlencoded'
    MULTIPART = 'multipart'
    RAW_BODY = 'raw_body'
    BYTES = 'bytes'
    PARAMS_ONLY = 'params_only'
    EMPTY = 'empty'


class RequestAnalyzer:
    """Analyze service configuration to determine request type."""
    
    @staticmethod
    def analyze(service: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze service and return detailed request information."""
        analysis = {
            'method': service.get('method', 'POST').upper(),
            'has_json': 'json' in service,
            'has_data': 'data' in service,
            'has_params': 'params' in service,
            'has_cookies': 'cookies' in service,
            'has_headers': 'headers' in service,
            'data_type': None,
            'data_value': None,
            'content_type': None,
            'request_type': None,
            'is_multipart': False,
            'is_raw_body': False,
            'has_boundary': False
        }
        
        # Extract Content-Type from headers
        if 'headers' in service:
            headers = service['headers']
            if isinstance(headers, dict):
                content_type = headers.get('Content-Type') or headers.get('content-type')
                if content_type:
                    analysis['content_type'] = content_type
                    if 'multipart' in content_type.lower():
                        analysis['is_multipart'] = True
                        analysis['has_boundary'] = 'boundary=' in content_type
        
        # Analyze data
        if 'data' in service:
            data = service['data']
            analysis['data_value'] = data
            
            if isinstance(data, dict):
                analysis['data_type'] = 'dict'
            elif isinstance(data, str):
                analysis['data_type'] = 'string'
                analysis['is_raw_body'] = True
                # Check for multipart boundary in string
                if 'boundary=' in data or 'Content-Disposition' in data:
                    analysis['is_multipart'] = True
                    analysis['has_boundary'] = True
            elif isinstance(data, (bytes, bytearray)):
                analysis['data_type'] = 'bytes'
            elif isinstance(data, (int, float, bool)):
                analysis['data_type'] = 'primitive'
            else:
                analysis['data_type'] = type(data).__name__
        
        # Determine request type
        analysis['request_type'] = RequestAnalyzer._determine_request_type(analysis)
        
        return analysis
    
    @staticmethod
    def _determine_request_type(analysis: Dict[str, Any]) -> str:
        """Determine the request type based on analysis."""
        # JSON takes precedence
        if analysis['has_json']:
            return RequestType.JSON
        
        # Check for raw body (pre-formatted data)
        if analysis['is_raw_body']:
            return RequestType.RAW_BODY
        
        # Check for bytes
        if analysis['data_type'] == 'bytes':
            return RequestType.BYTES
        
        # Check for form data
        if analysis['has_data'] and analysis['data_type'] == 'dict':
            # Use explicit Content-Type if present
            if analysis['content_type']:
                if 'form-urlencoded' in analysis['content_type'].lower():
                    return RequestType.FORM_URLENCODED
                elif 'multipart' in analysis['content_type'].lower():
                    return RequestType.MULTIPART
            return RequestType.FORM_DATA  # Default to form data
        
        # Check for params only
        if analysis['has_params'] and not analysis['has_data']:
            return RequestType.PARAMS_ONLY
        
        # Empty request
        if not analysis['has_data'] and not analysis['has_json'] and not analysis['has_params']:
            return RequestType.EMPTY
        
        # Default
        return RequestType.FORM_DATA


class RequestBuilder:
    """Build aiohttp request parameters based on service configuration."""
    
    @staticmethod
    def build(service: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Build request parameters for aiohttp."""
        request_params = {
            'method': analysis['method'],
            'url': service['url'],
            'timeout': 20  # Use int timeout for compatibility
        }
        
        # Add headers - preserve exactly as provided
        if 'headers' in service:
            headers = service['headers']
            if isinstance(headers, dict):
                request_params['headers'] = headers.copy()
        
        # Add cookies
        if 'cookies' in service:
            cookies = service['cookies']
            if isinstance(cookies, dict):
                request_params['cookies'] = cookies
        
        # Add params
        if 'params' in service:
            params = service['params']
            if isinstance(params, dict):
                request_params['params'] = params
        
        # Build body based on request type
        request_type = analysis['request_type']
        
        if request_type == RequestType.JSON:
            request_params['json'] = service['json']
        
        elif request_type == RequestType.FORM_DATA:
            # Form data as dict - aiohttp will handle it
            request_params['data'] = service['data']
        
        elif request_type == RequestType.FORM_URLENCODED:
            # Form-urlencoded - DO NOT override Content-Type if already set
            # Only set if not already present in headers
            if 'headers' not in request_params:
                request_params['headers'] = {}
            if 'Content-Type' not in request_params['headers'] and 'content-type' not in request_params['headers']:
                request_params['headers']['Content-Type'] = 'application/x-www-form-urlencoded'
            request_params['data'] = service['data']
        
        elif request_type == RequestType.MULTIPART:
            # Multipart form data
            data = service['data']
            if isinstance(data, bytes):
                # Pre-encoded bytes - use as-is
                request_params['data'] = data
            elif isinstance(data, dict):
                # Only convert to FormData if Content-Type not already set with boundary
                if analysis['content_type'] and 'boundary=' in analysis['content_type']:
                    # Service already has multipart with boundary - use as-is
                    request_params['data'] = data
                else:
                    # Convert dict to FormData
                    form_data = aiohttp.FormData()
                    for key, value in data.items():
                        form_data.add_field(key, value)
                    request_params['data'] = form_data
        
        elif request_type == RequestType.RAW_BODY:
            # Raw body string - use as-is
            request_params['data'] = service['data']
        
        elif request_type == RequestType.BYTES:
            # Raw bytes - use as-is
            request_params['data'] = service['data']
        
        elif request_type == RequestType.PARAMS_ONLY:
            # Only params - no body
            pass
        
        elif request_type == RequestType.EMPTY:
            # Empty request
            pass
        
        return request_params


class UniversalRequestHandler:
    """Universal handler for all HTTP request formats."""
    
    @staticmethod
    def analyze_service(service: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze service configuration."""
        return RequestAnalyzer.analyze(service)
    
    @staticmethod
    def build_request(service: Dict[str, Any]) -> Dict[str, Any]:
        """Build request parameters."""
        analysis = RequestAnalyzer.analyze(service)
        return RequestBuilder.build(service, analysis)
    
    @staticmethod
    async def send_request(session: aiohttp.ClientSession, service: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send HTTP request using universal handler.
        
        Returns:
            Dict with keys: status, success, error, response_text, status_code, request_type
        """
        analysis = RequestAnalyzer.analyze(service)
        request_params = RequestBuilder.build(service, analysis)
        
        try:
            async with session.request(**request_params) as response:
                status_code = response.status
                response_text = await response.text()
                
                # Determine success based on status code
                success = 200 <= status_code < 400
                
                return {
                    'status': 'success',
                    'success': success,
                    'error': None,
                    'response_text': response_text[:500],
                    'status_code': status_code,
                    'request_type': analysis['request_type'],
                    'method': analysis['method']
                }
                
        except aiohttp.ClientError as e:
            return {
                'status': 'error',
                'success': False,
                'error': f'ClientError: {str(e)}',
                'response_text': None,
                'status_code': None,
                'request_type': analysis['request_type'],
                'method': analysis['method']
            }
        except Exception as e:
            return {
                'status': 'error',
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'response_text': None,
                'status_code': None,
                'request_type': analysis['request_type'],
                'method': analysis['method']
            }


class RequestTypeClassifier:
    """Classifier for request types for debugging and analysis."""
    
    @staticmethod
    def classify(service: Dict[str, Any]) -> str:
        """Classify service into a human-readable type."""
        analysis = RequestAnalyzer.analyze(service)
        
        parts = [analysis['method']]
        
        # Add request type
        parts.append(analysis['request_type'].upper())
        
        # Add additional components
        if analysis['has_params']:
            parts.append('PARAMS')
        if analysis['has_cookies']:
            parts.append('COOKIES')
        if analysis['is_multipart']:
            parts.append('MULTIPART')
        
        return '_'.join(parts)
