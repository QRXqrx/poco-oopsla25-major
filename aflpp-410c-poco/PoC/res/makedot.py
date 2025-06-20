input_file = 'tog_analysis_edge'
output_file = 'graph.dot'

with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
    outfile.write("digraph G {\n")
    
    for line in infile:
        outfile.write(f"    {line.strip()};\n")
    
    outfile.write("}\n")
