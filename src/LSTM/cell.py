import numpy as np
from scipy.special import expit


class Cell:
    def __init__(self):
        return

    def forward(
            self,
            x,
            activ_prev,
            context_prev,
            weights,
            biases,
            take_input=True):

        if take_input:
            X = np.concatenate([activ_prev, x.reshape((-1, 1))], axis=0)
        else:
            x = activ_prev
            X = x

        forget_gate = expit((weights['forget'] @ X) + biases['forget'])
        update_gate = expit((weights['update'] @ X) + biases['update'])
        out_gate = expit((weights['output'] @ X) + biases['output'])
        candidate = np.tanh((weights['candidate'] @ X) + biases['candidate'])
        context = (forget_gate * context_prev) + (update_gate * candidate)
        activation = out_gate * np.tanh(context)

        # print(f'X {weights["forget"] @ X}')
        # print(f'biases {biases["forget"]}')
        # print(weights['forget'])
        # print(f'forget: {forget_gate}')
        # print(f'update: {update_gate}')
        # print(f'out: {out_gate}')
        # print(f'candidate: {candidate}')
        # print(f'context: {context}')
        # print(f'activation: {activation}')
        # 1/0

        cache = {
            "activation": activation,
            "context": context,
            "activ_prev": activ_prev,
            "context_prev": context_prev,
            "forget_gate": forget_gate,
            "update_gate": update_gate,
            "candidate": candidate,
            "out_gate": out_gate,
            "input": x,
            "weights": weights,
            "biases": biases
        }

        # print(f'forget_gate: {forget_gate.shape}')
        # print(f'X: {X.shape}')
        # print(f'weights out: {weights["output"].shape}')

        return activation, context, cache

    def backprop(self, dactivation, dcontext, cache, take_input=True):
        # activation = cache['activation']
        context = cache['context']
        activ_prev = cache['activ_prev']
        context_prev = cache['context_prev']
        forget_gate = cache['forget_gate']
        update_gate = cache['update_gate']
        out_gate = cache['out_gate']
        candidate = cache['candidate']
        x = cache['input']
        weights = cache['weights']

        out_len = context.shape[0]

        # print(f'context: {context.shape}')
        # print(f'out_gate: {out_gate.shape}')
        # Gradients for LSTM cell gates
        dcontext += dactivation * out_gate * (1 - np.square(np.tanh(context)))
        dout_gate = dactivation * np.tanh(context) * out_gate * (1 - out_gate)
        dforget_gate = (dcontext * context_prev) * forget_gate * (1 - forget_gate)
        dupdate_gate = (dcontext * candidate) * update_gate * (1 - update_gate)
        dcandidate = (dcontext * update_gate) * (1 - np.square(np.tanh(context)))

        if take_input:
            # print(f'xShape {x}')
            X = np.concatenate([activ_prev, x.reshape((-1, 1))], axis=0)
        else:
            X = activ_prev

        # print(dcontext[0][0])
        # print(dout_gate.shape)
        # print(X.shape)

        # Gradients for weights and biases
        dW_out = dout_gate @ X.T
        db_out = np.sum(dout_gate, axis=1, keepdims=True)
        dW_update = dupdate_gate @ X.T
        db_update = np.sum(dupdate_gate, axis=1, keepdims=True)
        dW_forget = dforget_gate @ X.T
        db_forget = np.sum(dforget_gate, axis=1, keepdims=True)
        dW_candidate = dcandidate @ X.T
        db_candidate = np.sum(dcandidate, axis=1, keepdims=True)

        # Gradients for previous time-step activation
        # print(f'weights {dW_forget[:10, :10]}')
        # print(f'gate {dforget_gate[:10, :10]}')
        dx_forget = (weights['forget'].T @ dforget_gate) / 1e-4
        dx_update = (weights['update'].T @ dupdate_gate) / 1e-4
        dx_out = (weights['output'].T @ dout_gate) / 1e-4
        dx_candidate = (weights['candidate'].T @ dcandidate) / 1e-4
        dx = (dx_forget + dx_update + dx_out + dx_candidate) / 4

        dactiv_prev = dx[:out_len, :]
        dcontext_prev = dcontext * forget_gate

        # print(f'dactivation_prev: {dactiv_prev.shape}')
        # print(((weights['forget'][:, out_len:].T @ dforget_gate) + (weights['update'][:, out_len:].T @ dupdate_gate) + (weights['candidate'][:, out_len:].T @ dcandidate) + (weights['output'][:, out_len:].T @ dout_gate)).shape)

        # print(dactiv_prev[0][0])

        # Gradients compiled into single dict
        gradients = {
            'input': dx,
            'activ_prev': dactiv_prev,
            'context_prev': dcontext_prev,
            'weights_forget': dW_forget,
            'weights_update': dW_update,
            'weights_output': dW_out,
            'weights_candidate': dW_candidate,
            'bias_forget': db_forget,
            'bias_update': db_update,
            'bias_output': db_out,
            'bias_candidate': db_candidate,
        }

        gradients = clip_gradients(gradients)
        return gradients


def clip_gradients(grads):
    for k, v in grads.items():
        np.clip(
            v, 1e-3, 1e3, out=grads[k]
        )
    return grads
