import torch
from torch.nn import Parameter
from torch_geometric.nn import ChebConv
from torch_geometric.nn.inits import glorot, zeros


class GConvGRU(torch.nn.Module):
    r"""An implementation of the Chebyshev Graph Convolutional Gated Recurrent Unit
    Cell. For details see this paper: `"Structured Sequence Modeling with Graph 
    Convolutional Recurrent Networks." <https://arxiv.org/abs/1612.07659>`_

    Args:
        in_channels (int): Number of input features.
        out_channels (int): Number of output features.
        K (int): Chebyshev filter size.
        number_of_nodes (int): Number of vertices in the graph.
    """
    def __init__(self, in_channels, out_channels, K, number_of_nodes):
        super(GConvGRU, self).__init__()

        self.in_channels = in_channels
        self.out_channels = out_channels
        self.K = K
        self.number_of_nodes = number_of_nodes

        self._create_parameters_and_layers()


    def _create_update_gate_parameters_and_layers(self):

        self.conv_x_z = ChebConv(in_channels=self.in_channels,
                                 out_channels=self.out_channels,
                                 K=self.K)

        self.conv_h_z = ChebConv(in_channels=self.out_channels,
                                 out_channels=self.out_channels,
                                 K=self.K) 


    def _create_reset_gate_parameters_and_layers(self):

        self.conv_x_r = ChebConv(in_channels=self.in_channels,
                                 out_channels=self.out_channels,
                                 K=self.K)

        self.conv_h_r = ChebConv(in_channels=self.out_channels,
                                 out_channels=self.out_channels,
                                 K=self.K)


    def _create_candidate_state_parameters_and_layers(self):

        self.conv_x_h = ChebConv(in_channels=self.in_channels,
                                 out_channels=self.out_channels,
                                 K=self.K)

        self.conv_h_h = ChebConv(in_channels=self.out_channels,
                                 out_channels=self.out_channels,
                                 K=self.K)


    def _create_parameters_and_layers(self):
        self._create_input_gate_parameters_and_layers()
        self._create_forget_gate_parameters_and_layers()
        self._create_cell_state_parameters_and_layers()



    def _set_hidden_state(self, X, H):
        if H is None:
            H = torch.zeros(self.number_of_nodes, self.out_channels)
        return H

    def _calculate_input_gate(self, X, edge_index, edge_weight, H, C):
        I = self.conv_x_i(X, edge_index, edge_weight)
        I = I + self.conv_h_i(H, edge_index, edge_weight)
        I = I + (self.w_c_i * C)
        I = I + self.b_i
        I = torch.sigmoid(I) 
        return I


    def _calculate_forget_gate(self, X, edge_index, edge_weight, H, C):
        F = self.conv_x_f(X, edge_index, edge_weight)
        F = F + self.conv_h_f(H, edge_index, edge_weight)
        F = F + (self.w_c_f * C)
        F = F + self.b_f
        F = torch.sigmoid(F) 
        return F


    def _calculate_cell_state(self, X, edge_index, edge_weight, H, C, I, F):
        T = self.conv_x_c(X, edge_index, edge_weight)
        T = T + self.conv_h_c(T, edge_index, edge_weight)
        T = T + self.b_c
        T = torch.tanh(T)
        C = F*C + I*T  
        return C

    def _calculate_output_gate(self, X, edge_index, edge_weight, H, C):
        O = self.conv_x_o(X, edge_index, edge_weight)
        O = O + self.conv_h_o(H, edge_index, edge_weight)
        O = O + (self.w_c_o * C)
        O = O + self.b_o
        O = torch.sigmoid(O) 
        return O


    def _calculate_hidden_state(self, O, C):
        H = O * torch.tanh(C)
        return H


    def forward(self, X, edge_index, edge_weight=None, H=None):
        """
        Making a forward pass. If edge weights are not present the forward pass
        defaults to an unweighted graph. If the hidden state and cell state 
        matrices are not present when the forward pass is called these are
        initialized with zeros.

        Arg types:
            * **X** *(PyTorch Float Tensor)* - Node features.
            * **edge_index** *(PyTorch Long Tensor)* - Graph edge indices.
            * **edge_weight** *(PyTorch Long Tensor)* - Edge weight vector (optional).
            * **H** *(PyTorch Float Tensor)* - Hidden state matrix for all nodes (optional).

        Return types:
            * **H** *(PyTorch Float Tensor)* - Hidden state matrix for all nodes.
        """
        H = self._set_hidden_state(X, H)
        C = self._set_cell_state(X, C)
        I = self._calculate_input_gate(X, edge_index, edge_weight, H, C)
        F = self._calculate_forget_gate(X, edge_index, edge_weight, H, C)
        C = self._calculate_cell_state(X, edge_index, edge_weight, H, C, I, F)
        O = self._calculate_output_gate(X, edge_index, edge_weight, H, C)
        H = self._calculate_hidden_state(O, C)
        return H, C
    
