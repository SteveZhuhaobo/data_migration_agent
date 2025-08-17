import graphviz
##import os
##os.environ["PATH"] += os.pathsep + r"C:\Program Files\Graphviz\bin"
# Create a simple directed graph
dot = graphviz.Digraph(comment="Simple Test Graph")

dot.node("A", "Start")
dot.node("B", "End")
dot.edge("A", "B", label="goes to")

# Render to PNG file
dot.render("simple_graph", format="png", cleanup=True)

print("Graph generated: simple_graph.png")
