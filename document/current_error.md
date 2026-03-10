
Used following env

set FORMATTER_READ_TIMEOUT=400
set FORMATTER_MAX_JSON_BYTES=50000   # forces chunked for your 74KB payload
set FORMATTER_MAX_CONCURRENCY=2
set FORMATTER_MAX_ATTEMPTS=3

set KNOWLEDGE_BASE_ID=1NR6BI4TNO
set AWS_REGION=us-east-2
set RESEARCH_MAX_TOKENS=15000
set RESEARCH_MAX_ATTEMPTS=2
set CONTENT_MAX_TOKENS = 7000
set CONTENT_MAX_TOKENS_PER_SECTION=6000
set CONTENT_MAX_FACTS_PER_SECTION=10
set CONTENT_MAX_CITES_PER_SECTION=6
set FORMATTING_MAX_TOKENS =7000
set FORMATTER_MAX_JSON_BYTES=100000
set CONTENT_MAX_JSON_BYTES=100000
set FORMATTER_MAX_CONCURRENCY = 2
set FORMATTER_READ_TIMEOUT = 400
set FORMATTER_MAX_ATTEMPTS = 5



All 9 sections have been generated and stored in `SOPState.content_sections` for `workflow_id::sop-8558994228268727304`. The pipeline is ready to proceed to the next node (e.g., **review**, **formatting**, or **finalization**).
Tool #1: run_formatting
2026-03-10 13:59:14 - src.agents.formatter_agent - INFO - >>> run_formatting | prompt: Original Task: workflow_id::sop-8558994228268727304 | Generate a Standard Operating Procedure for: Global Technology Inf
2026-03-10 13:59:14 - src.agents.formatter_agent - INFO - Formatter payload size ~73899 bytes | sections=9
2026-03-10 13:59:14 - src.agents.formatter_agent - INFO - Payload within limit — using single-shot whole-document formatting.
2026-03-10 13:59:14 - botocore.credentials - INFO - Found credentials in shared credentials file: C:\Users\cr242786\sop-strands-agent - poc\app\.aws\credentials
2026-03-10 14:02:29 - src.agents.formatter_agent - WARNING - LLM call failed | attempt=1/5 | will retry in 1.05s | error=
2026-03-10 14:05:45 - src.agents.formatter_agent - WARNING - LLM call failed | attempt=2/5 | will retry in 1.70s | error=
2026-03-10 14:09:02 - src.agents.formatter_agent - WARNING - LLM call failed | attempt=3/5 | will retry in 2.71s | error=
2026-03-10 14:09:19 - asyncio - ERROR - Task exception was never retrieved
future: <Task finished name='Task-6058' coro=<to_thread() done, defined at C:\Python311\Lib\asyncio\threads.py:12> exception=ReadTimeoutError('Read timeout on endpoint URL: "https://bedrock-runtime.us-east-2.amazonaws.com/model/arn%3Aaws%3Abedrock%3Aus-east-2%3A070797854596%3Ainference-profile%2Fglobal.anthropic.claude-sonnet-4-6/converse"')>
Traceback (most recent call last):
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\urllib3\connectionpool.py", line 534, in _make_request
    response = conn.getresponse()
               ^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\urllib3\connection.py", line 571, in getresponse
    httplib_response = super().getresponse()
                       ^^^^^^^^^^^^^^^^^^^^^
  File "C:\Python311\Lib\http\client.py", line 1374, in getresponse
    response.begin()
  File "C:\Python311\Lib\http\client.py", line 318, in begin
    version, status, reason = self._read_status()
                              ^^^^^^^^^^^^^^^^^^^
  File "C:\Python311\Lib\http\client.py", line 279, in _read_status
    line = str(self.fp.readline(_MAXLINE + 1), "iso-8859-1")
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Python311\Lib\socket.py", line 705, in readinto
    return self._sock.recv_into(b)
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Python311\Lib\ssl.py", line 1278, in recv_into
    return self.read(nbytes, buffer)
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Python311\Lib\ssl.py", line 1134, in read
    return self._sslobj.read(len, buffer)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TimeoutError: The read operation timed out

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\httpsession.py", line 477, in send
    urllib_response = conn.urlopen(
                      ^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\urllib3\connectionpool.py", line 841, in urlopen
    retries = retries.increment(
              ^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\urllib3\util\retry.py", line 449, in increment
    raise reraise(type(error), error, _stacktrace)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\urllib3\util\util.py", line 39, in reraise
    raise value
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\urllib3\connectionpool.py", line 787, in urlopen
    response = self._make_request(
               ^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\urllib3\connectionpool.py", line 536, in _make_request
    self._raise_timeout(err=e, url=url, timeout_value=read_timeout)
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\urllib3\connectionpool.py", line 367, in _raise_timeout
    raise ReadTimeoutError(
urllib3.exceptions.ReadTimeoutError: AWSHTTPSConnectionPool(host='bedrock-runtime.us-east-2.amazonaws.com', port=443): Read timed out. (read timeout=120)

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "C:\Python311\Lib\asyncio\threads.py", line 25, in to_thread
    return await loop.run_in_executor(None, func_call)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Python311\Lib\concurrent\futures\thread.py", line 58, in run
    result = self.fn(*self.args, **self.kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\opentelemetry\instrumentation\threading\__init__.py", line 171, in wrapped_func
    return original_func(*func_args, **func_kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\strands\models\bedrock.py", line 722, in _stream
    response = self.client.converse(**request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\client.py", line 602, in _api_call
    return self._make_api_call(operation_name, kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\context.py", line 123, in wrapper
    return func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\client.py", line 1060, in _make_api_call
    http, parsed_response = self._make_request(
                            ^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\client.py", line 1084, in _make_request
    return self._endpoint.make_request(operation_model, request_dict)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\endpoint.py", line 119, in make_request
    return self._send_request(request_dict, operation_model)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\endpoint.py", line 200, in _send_request
    while self._needs_retry(
          ^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\endpoint.py", line 360, in _needs_retry
    responses = self._event_emitter.emit(
                ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\hooks.py", line 412, in emit
    return self._emitter.emit(aliased_event_name, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\hooks.py", line 256, in emit
    return self._emit(event_name, kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\hooks.py", line 239, in _emit
    response = handler(**kwargs)
               ^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\retryhandler.py", line 207, in __call__
    if self._checker(**checker_kwargs):
       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\retryhandler.py", line 284, in __call__
    should_retry = self._should_retry(
                   ^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\retryhandler.py", line 320, in _should_retry
    return self._checker(attempt_number, response, caught_exception)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\retryhandler.py", line 363, in __call__
    checker_response = checker(
                       ^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\retryhandler.py", line 247, in __call__
    return self._check_caught_exception(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\retryhandler.py", line 416, in _check_caught_exception
    raise caught_exception
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\endpoint.py", line 279, in _do_get_response
    http_response = self._send(request)
                    ^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\endpoint.py", line 383, in _send
    return self.http_session.send(request)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\httpsession.py", line 514, in send
    raise ReadTimeoutError(endpoint_url=request.url, error=e)
botocore.exceptions.ReadTimeoutError: Read timeout on endpoint URL: "https://bedrock-runtime.us-east-2.amazonaws.com/model/arn%3Aaws%3Abedrock%3Aus-east-2%3A070797854596%3Ainference-profile%2Fglobal.anthropic.claude-sonnet-4-6/converse"
2026-03-10 14:12:19 - src.agents.formatter_agent - WARNING - LLM call failed | attempt=4/5 | will retry in 4.30s | error=
2026-03-10 14:12:34 - asyncio - ERROR - Task exception was never retrieved
future: <Task finished name='Task-7847' coro=<to_thread() done, defined at C:\Python311\Lib\asyncio\threads.py:12> exception=ReadTimeoutError('Read timeout on endpoint URL: "https://bedrock-runtime.us-east-2.amazonaws.com/model/arn%3Aaws%3Abedrock%3Aus-east-2%3A070797854596%3Ainference-profile%2Fglobal.anthropic.claude-sonnet-4-6/converse"')>
Traceback (most recent call last):
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\urllib3\connectionpool.py", line 534, in _make_request
    response = conn.getresponse()
               ^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\urllib3\connection.py", line 571, in getresponse
    httplib_response = super().getresponse()
                       ^^^^^^^^^^^^^^^^^^^^^
  File "C:\Python311\Lib\http\client.py", line 1374, in getresponse
    response.begin()
  File "C:\Python311\Lib\http\client.py", line 318, in begin
    version, status, reason = self._read_status()
                              ^^^^^^^^^^^^^^^^^^^
  File "C:\Python311\Lib\http\client.py", line 279, in _read_status
    line = str(self.fp.readline(_MAXLINE + 1), "iso-8859-1")
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Python311\Lib\socket.py", line 705, in readinto
    return self._sock.recv_into(b)
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Python311\Lib\ssl.py", line 1278, in recv_into
    return self.read(nbytes, buffer)
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Python311\Lib\ssl.py", line 1134, in read
    return self._sslobj.read(len, buffer)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TimeoutError: The read operation timed out

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\httpsession.py", line 477, in send
    urllib_response = conn.urlopen(
                      ^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\urllib3\connectionpool.py", line 841, in urlopen
    retries = retries.increment(
              ^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\urllib3\util\retry.py", line 449, in increment
    raise reraise(type(error), error, _stacktrace)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\urllib3\util\util.py", line 39, in reraise
    raise value
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\urllib3\connectionpool.py", line 787, in urlopen
    response = self._make_request(
               ^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\urllib3\connectionpool.py", line 536, in _make_request
    self._raise_timeout(err=e, url=url, timeout_value=read_timeout)
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\urllib3\connectionpool.py", line 367, in _raise_timeout
    raise ReadTimeoutError(
urllib3.exceptions.ReadTimeoutError: AWSHTTPSConnectionPool(host='bedrock-runtime.us-east-2.amazonaws.com', port=443): Read timed out. (read timeout=120)

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "C:\Python311\Lib\asyncio\threads.py", line 25, in to_thread
    return await loop.run_in_executor(None, func_call)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Python311\Lib\concurrent\futures\thread.py", line 58, in run
    result = self.fn(*self.args, **self.kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\opentelemetry\instrumentation\threading\__init__.py", line 171, in wrapped_func
    return original_func(*func_args, **func_kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\strands\models\bedrock.py", line 722, in _stream
    response = self.client.converse(**request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\client.py", line 602, in _api_call
    return self._make_api_call(operation_name, kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\context.py", line 123, in wrapper
    return func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\client.py", line 1060, in _make_api_call
    http, parsed_response = self._make_request(
                            ^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\client.py", line 1084, in _make_request
    return self._endpoint.make_request(operation_model, request_dict)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\endpoint.py", line 119, in make_request
    return self._send_request(request_dict, operation_model)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\endpoint.py", line 200, in _send_request
    while self._needs_retry(
          ^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\endpoint.py", line 360, in _needs_retry
    responses = self._event_emitter.emit(
                ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\hooks.py", line 412, in emit
    return self._emitter.emit(aliased_event_name, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\hooks.py", line 256, in emit
    return self._emit(event_name, kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\hooks.py", line 239, in _emit
    response = handler(**kwargs)
               ^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\retryhandler.py", line 207, in __call__
    if self._checker(**checker_kwargs):
       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\retryhandler.py", line 284, in __call__
    should_retry = self._should_retry(
                   ^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\retryhandler.py", line 320, in _should_retry
    return self._checker(attempt_number, response, caught_exception)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\retryhandler.py", line 363, in __call__
    checker_response = checker(
                       ^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\retryhandler.py", line 247, in __call__
    return self._check_caught_exception(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\retryhandler.py", line 416, in _check_caught_exception
    raise caught_exception
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\endpoint.py", line 279, in _do_get_response
    http_response = self._send(request)
                    ^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\endpoint.py", line 383, in _send
    return self.http_session.send(request)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\httpsession.py", line 514, in send
    raise ReadTimeoutError(endpoint_url=request.url, error=e)
botocore.exceptions.ReadTimeoutError: Read timeout on endpoint URL: "https://bedrock-runtime.us-east-2.amazonaws.com/model/arn%3Aaws%3Abedrock%3Aus-east-2%3A070797854596%3Ainference-profile%2Fglobal.anthropic.claude-sonnet-4-6/converse"
2026-03-10 14:15:39 - src.agents.formatter_agent - WARNING - LLM call failed | attempt=5/5 | will retry in 6.80s | error=
2026-03-10 14:15:39 - src.agents.formatter_agent - ERROR - Formatting FAILED: LLM call failed after 5 attempts:
Traceback (most recent call last):
  File "C:\Users\cr242786\sop-strands-agent - poc\app\src\agents\formatter_agent.py", line 378, in run_formatting
    formatted_doc = await _run_llm_formatter(state)
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent - poc\app\src\agents\formatter_agent.py", line 353, in _run_llm_formatter
    return await _run_llm_formatter_whole(state)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent - poc\app\src\agents\formatter_agent.py", line 230, in _run_llm_formatter_whole
    text = await _invoke_with_retries(llm, user_prompt)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent - poc\app\src\agents\formatter_agent.py", line 195, in _invoke_with_retries
    raise RuntimeError(f"LLM call failed after {_MAX_ATTEMPTS} attempts: {last_err}")
RuntimeError: LLM call failed after 5 attempts:
2026-03-10 14:15:52 - asyncio - ERROR - Task exception was never retrieved
future: <Task finished name='Task-9645' coro=<to_thread() done, defined at C:\Python311\Lib\asyncio\threads.py:12> exception=ReadTimeoutError('Read timeout on endpoint URL: "https://bedrock-runtime.us-east-2.amazonaws.com/model/arn%3Aaws%3Abedrock%3Aus-east-2%3A070797854596%3Ainference-profile%2Fglobal.anthropic.claude-sonnet-4-6/converse"')>
Traceback (most recent call last):
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\urllib3\connectionpool.py", line 534, in _make_request
    response = conn.getresponse()
               ^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\urllib3\connection.py", line 571, in getresponse
    httplib_response = super().getresponse()
                       ^^^^^^^^^^^^^^^^^^^^^
  File "C:\Python311\Lib\http\client.py", line 1374, in getresponse
    response.begin()
  File "C:\Python311\Lib\http\client.py", line 318, in begin
    version, status, reason = self._read_status()
                              ^^^^^^^^^^^^^^^^^^^
  File "C:\Python311\Lib\http\client.py", line 279, in _read_status
    line = str(self.fp.readline(_MAXLINE + 1), "iso-8859-1")
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Python311\Lib\socket.py", line 705, in readinto
    return self._sock.recv_into(b)
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Python311\Lib\ssl.py", line 1278, in recv_into
    return self.read(nbytes, buffer)
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Python311\Lib\ssl.py", line 1134, in read
    return self._sslobj.read(len, buffer)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TimeoutError: The read operation timed out

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\httpsession.py", line 477, in send
    urllib_response = conn.urlopen(
                      ^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\urllib3\connectionpool.py", line 841, in urlopen
    retries = retries.increment(
              ^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\urllib3\util\retry.py", line 449, in increment
    raise reraise(type(error), error, _stacktrace)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\urllib3\util\util.py", line 39, in reraise
    raise value
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\urllib3\connectionpool.py", line 787, in urlopen
    response = self._make_request(
               ^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\urllib3\connectionpool.py", line 536, in _make_request
    self._raise_timeout(err=e, url=url, timeout_value=read_timeout)
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\urllib3\connectionpool.py", line 367, in _raise_timeout
    raise ReadTimeoutError(
urllib3.exceptions.ReadTimeoutError: AWSHTTPSConnectionPool(host='bedrock-runtime.us-east-2.amazonaws.com', port=443): Read timed out. (read timeout=120)

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "C:\Python311\Lib\asyncio\threads.py", line 25, in to_thread
    return await loop.run_in_executor(None, func_call)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Python311\Lib\concurrent\futures\thread.py", line 58, in run
    result = self.fn(*self.args, **self.kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\opentelemetry\instrumentation\threading\__init__.py", line 171, in wrapped_func
    return original_func(*func_args, **func_kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\strands\models\bedrock.py", line 722, in _stream
    response = self.client.converse(**request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\client.py", line 602, in _api_call
    return self._make_api_call(operation_name, kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\context.py", line 123, in wrapper
    return func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\client.py", line 1060, in _make_api_call
    http, parsed_response = self._make_request(
                            ^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\client.py", line 1084, in _make_request
    return self._endpoint.make_request(operation_model, request_dict)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\endpoint.py", line 119, in make_request
    return self._send_request(request_dict, operation_model)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\endpoint.py", line 200, in _send_request
    while self._needs_retry(
          ^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\endpoint.py", line 360, in _needs_retry
    responses = self._event_emitter.emit(
                ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\hooks.py", line 412, in emit
    return self._emitter.emit(aliased_event_name, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\hooks.py", line 256, in emit
    return self._emit(event_name, kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\hooks.py", line 239, in _emit
    response = handler(**kwargs)
               ^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\retryhandler.py", line 207, in __call__
    if self._checker(**checker_kwargs):
       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\retryhandler.py", line 284, in __call__
    should_retry = self._should_retry(
                   ^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\retryhandler.py", line 320, in _should_retry
    return self._checker(attempt_number, response, caught_exception)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\retryhandler.py", line 363, in __call__
    checker_response = checker(
                       ^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\retryhandler.py", line 247, in __call__
    return self._check_caught_exception(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\retryhandler.py", line 416, in _check_caught_exception
    raise caught_exception
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\endpoint.py", line 279, in _do_get_response
    http_response = self._send(request)
                    ^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\endpoint.py", line 383, in _send
    return self.http_session.send(request)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\httpsession.py", line 514, in send
    raise ReadTimeoutError(endpoint_url=request.url, error=e)
botocore.exceptions.ReadTimeoutError: Read timeout on endpoint URL: "https://bedrock-runtime.us-east-2.amazonaws.com/model/arn%3Aaws%3Abedrock%3Aus-east-2%3A070797854596%3Ainference-profile%2Fglobal.anthropic.claude-sonnet-4-6/converse"
⚠️ **Formatting Node — Status Update**

| Field | Detail |
|---|---|
| **Workflow ID** | `sop-8558994228268727304` |
| **Node** | Formatting |
| **Status** | ❌ FAILED |
| **Reason** | LLM call failed after 5 attempts |

---

### ⚠️ What This Means

The **Formatting Node** was unable to apply the final document formatting to the 9 content sections generated for the **Global Technology Infrastructure Qualification SOP**. The underlying LLM service did not return a successful response after **5 retry attempts**.

---

### 🔁 Recommended Next Steps

1. **Retry Formatting** — Re-trigger the formatting node for `workflow_id::sop-8558994228268727304`. The content sections are safely stored in `SOPState.content_sections` and do not need to be regenerated.
2. **Check LLM Service Health** — Verify that the connected LLM endpoint is operational and reachable.
3. **Inspect Logs** — Review pipeline logs for `sop-8558994228268727304` to identify whether the failure is due to a timeout, rate limit, token limit, or service outage.
4. **Escalate if Persistent** — If retries continue to fail, escalate to the pipeline infrastructure team for diagnosis.

---

> ✅ **Note:** All 9 SOP sections (Purpose, Scope, Roles & Responsibilities, Regulatory & Compliance References, Definitions & Abbreviations, Procedure, Documentation & Evidence Requirements, Training Requirements, and Document Control) remain intact in `SOPState` and are ready for formatting once the issue is resolved.
Tool #1: run_qa
2026-03-10 14:15:59 - src.agents.qa_agent - ERROR - QA review failed: No formatted document available for QA review
**QA Node — Status Update**

| Field | Detail |
|---|---|
| **Workflow ID** | `sop-8558994228268727304` |
| **Node** | Quality Assurance |
| **Status** | ❌ FAILED |
| **Reason** | No formatted document available for QA review |

