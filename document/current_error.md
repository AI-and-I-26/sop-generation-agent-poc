node_id=<planning>, error=<Node 'planning' of type '<class 'strands.tools.decorator.DecoratedFunctionTool'>' is not supported> | node failed
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
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\strands\multiagent\graph.py", line 880, in _execute_node
    raise ValueError(f"Node '{node.node_id}' of type '{type(node.executor)}' is not supported")
ValueError: Node 'planning' of type '<class 'strands.tools.decorator.DecoratedFunctionTool'>' is not supported
✅ Generation complete!
   Status: failed
   File: sop_chemical_spill_response.md
   Size: 0 characters
