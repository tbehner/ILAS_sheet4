#!/usr/bin/env python3 
import random
import itertools
import math
from optparse import OptionParser

parser = OptionParser()
parser.add_option("-e", "--eta", dest="eta_value", help="size of steps", metavar="VALUE", type="float", default=0.01)
parser.add_option("-m", "--maxiter", dest="max_iterations", help="maximum number of iterations", metavar="NUMBER", type="int", default=1000000)
parser.add_option("-t", "--threshold", dest="iter_threshold", help="threshold of errors", metavar="VALUE", type="float", default=0)
(options,args) = parser.parse_args()

class Example:
    def __init__(self,input_values, outcome):
        self.input_values = input_values
        self.outcome      = outcome

    def __str__(self):
        return str(self.input_values) + " : " + str(self.outcome)

random.seed(0)
def small_random_value():
    return round(random.uniform(-2,2),2)

class Neuron:
    def __init__(self,idx,predecessors=[],successors=[]):
        self.idx            = idx
        self.is_input_node  = False
        self.is_output_node = False
        self.bias_node      = False
        self.input_value    = 0
        self.output_value   = 0
        self.predecessors   = predecessors
        self.successors     = successors
        self.weights        = []

    def initialize_weights(self):
        self.weights = [ small_random_value() for s in self.successors ]

    def set_is_input_node(value):
        self.is_input_node = value

    def set_is_output_node(value):
        self.is_output_node = value

    def __str__(self):
        return "{} : ({})".format(self.idx,", ".join([str((item,round(self.weights[i],3))) for i,item in enumerate(self.successors)]))

def sigmoid(x):
    return 1/(1+math.exp((-1)*x))

class NeuronalNetwork:
    def __init__(self,num_input_nodes,hidden_nodes_desc,num_output_nodes):
        """ 
        hidden_nodes_desc expects a list of numbers. The number on the ith
        positions states the number of neurons in the ith layer.
        """
        self.nodes = []
        self.input_nodes  = []
        self.hidden_nodes = []
        self.output_nodes = []
        self.bias_nodes_idx = []
        self.idx = 0

        # create input nodes
        for i in range(num_input_nodes):
            input_neuron = Neuron(self.idx)
            self.idx += 1
            self.input_nodes.append(input_neuron)
        self.nodes += self.input_nodes

        # create hidden neurons from description given by hidden_nodes_desc
        self.layers = []
        for num in hidden_nodes_desc:
            new_layer = []
            for i in range(num+1):
                hidden_neuron = Neuron(self.idx)
                self.idx += 1
                new_layer.append(hidden_neuron)
                self.hidden_nodes.append(hidden_neuron)
                # mark the last node as bias node
                if i == range(num):
                  hidden_neuron.bias_node = True
                  self.bias_nodes_ids.append(hidden_neuron.idx)
            self.layers.append(new_layer)
        self.nodes += self.hidden_nodes

        # create output nodes 
        for i in range(num_output_nodes):
            output_neuron = Neuron(self.idx)
            self.idx+=1
            self.output_nodes.append(output_neuron)
        self.nodes += self.output_nodes

        # connect the input nodes with the nodes in the first hidden layer
        for node in self.input_nodes:
            node.successors = [node.idx for node in self.layers[0]]
        # connect the nodes in the ith hidden layer with the nodes in the (i+1)th hidden layer
        for idx, layer in enumerate(self.layers):
            if idx == len(self.layers)-1:
                break
            following_layer = self.layers[idx+1]
            for node in layer:
                node.successors = [ node.idx for node in following_layer ]
            for node in following_layer:
                node.predecessors = [ node.idx for node in layer ]

        # connect the nodes in the last hidden layer with the output nodes
        last_hidden_layer = self.layers[-1]
        for node in last_hidden_layer:
            node.successors = [node.idx for node in self.output_nodes]
        for output_node in self.output_nodes:
            output_node.predecessors = [ node.idx for node in last_hidden_layer ]

        for node in self.nodes:
            node.initialize_weights()
        # TODO: do we need additional input nodes with fixed input like in the lecture?

    def forward_propagation(self,example):
        # whipe out any results (inputs/outputs) left over from previous runs
        for node in self.nodes:
            node.input_value = 0
            node.output_value = 0
        for idx in self.bias_nodes_idx:
          self.nodes[idx].output_value = 1

        # initialize output of input_nodes from the example
        for idx in range(len(self.input_nodes)):
            self.nodes[idx].output_value = example.input_values[idx]

        # forward propagation on input nodes
        for input_node in self.input_nodes:
            for idx, suc in enumerate(input_node.successors):
                successor = self.nodes[suc]
                successor.input_value += input_node.weights[idx] * input_node.output_value

        # forward propagation on each hidden layer
        for layer in self.layers:
            for node in layer:
                if not node.idx in self.bias_nodes_idx:
                    node.output_value = sigmoid(node.input_value)
                for idx, suc in enumerate(node.successors):
                    self.nodes[suc].input_value += node.weights[idx] * node.output_value

        # ouput computation on output nodes
        for node in self.output_nodes:
            node.output_value = sigmoid(node.input_value)


    def backward_propagation(self,examples,eta,maxiter,threshold):
        descended = True
        delta = [0] * len(self.nodes)
        iteration = 0
        # while termination criterion not fullfilled
        while descended and iteration < maxiter:
            descended = False
            iteration += 1
            for example in examples:
                # Step 1 : forward propagation with example
                self.forward_propagation(example)

                # Step 2 : compute delta on output units
                for node in self.output_nodes:
                    delta[node.idx] = node.output_value*(1-node.output_value)*(example.outcome-node.output_value)

                # Step 3 : compute delta for each node in each hidden layer
                for node in reversed(self.hidden_nodes):
                    # compute sum
                    sum_v = 0
                    for idx, suc in enumerate(node.successors):
                        sum_v += delta[suc]*node.weights[idx]
                    delta[node.idx] = node.output_value*(1-node.output_value)*sum_v

                # Step 4 : update network weights
                for node in self.nodes:
                    for idx in range(len(node.weights)):
                        delta_weight = eta * delta[node.successors[idx]] *  node.output_value
                        node.weights[idx] += delta_weight
                        if delta_weight > threshold:
                            descended = True


    def __str__(self):
        ret_string = ""
        ret_string += "Input nodes: \n"
        for node in self.input_nodes:
            ret_string += str(node) + "\n"
        for idx, layer in enumerate(self.layers):
            ret_string += "Layer " + str(idx) + " : \n"
            for node in layer:
                ret_string += str(node) + "\n"
        ret_string += "Output nodes: \n"
        for node in self.output_nodes:
            ret_string += str(node) + "\n"
        return ret_string


# logical function to be learned
def xor(x,a,b):
    return 1 if bool(a) != bool(b) else 0

def generate_examples(logical_func,n_args):
    examples = []
    for x in itertools.product('01',repeat=n_args):
        # bias value
        arguments = [1]
        arguments += [int(i) for i in x]
        examples.append(Example(arguments,logical_func(*arguments)))
    return examples

if __name__ == "__main__":
  nn = NeuronalNetwork(3,[2],1)
  examples = generate_examples(xor,2)
  print(nn)
  nn.backward_propagation(examples,options.eta_value,options.max_iterations,options.iter_threshold)
  print(nn)
  for example in examples:
      print(example)
      nn.forward_propagation(example)
      print(nn.output_nodes[0].output_value)

