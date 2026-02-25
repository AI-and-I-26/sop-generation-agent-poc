node_id=<planning>, error=<Input prompt must be of type: `str | list[Contentblock] | Messages | None`.> | node failed
graph execution failed
Traceback (most recent call last):
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\strands\multiagent\graph.py", line 555, in stream_async
    async for event in self._execute_graph(invocation_state):
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\strands\multiagent\graph.py", line 613, in _execute_graph
    async for event in self._execute_nodes_parallel(current_batch, invocation_state):
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\strands\multiagent\graph.py", line 678, in _execute_nodes_parallel   
    raise event
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\strands\multiagent\graph.py", line 716, in _stream_node_to_queue     
    async for event in self._execute_node(node, invocation_state):
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\strands\multiagent\graph.py", line 845, in _execute_node
    async for event in node.executor.stream_async(node_input, invocation_state=invocation_state):
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\strands\agent\agent.py", line 580, in stream_async
    messages = await self._convert_prompt_to_messages(prompt)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\strands\agent\agent.py", line 750, in _convert_prompt_to_messages    
    raise ValueError("Input prompt must be of type: `str | list[Contentblock] | Messages | None`.")
ValueError: Input prompt must be of type: `str | list[Contentblock] | Messages | None`.
Workflow failed: Input prompt must be of type: `str | list[Contentblock] | Messages | None`.
✅ Generation complete!
   Status: failed
   File: sop_chemical_spill_response.md
   Size: 0 characters
