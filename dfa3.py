from graphviz import Digraph
import copy


class DFA:
    def __init__(self, states, alphabets, init_state, final_states, transition_funct):
        self.states = states
        self.alphabets = alphabets
        self.init_state = init_state
        self.final_states = final_states
        self.transition_funct = transition_funct
        self.ds = {}
        self.transition_dict = {}
        self.set_transition_dict()

    def draw_graph(self, label, name):
        gr = Digraph(format='svg')
        gr.attr(rankdir='LR')
        gr.attr('node', shape='point')
        gr.node('qi')
        for i in self.states:
            if i in self.final_states:
                gr.attr('node', shape='doublecircle', color='green', style='')
            elif i in self.init_state:
                gr.attr('node', shape='circle', color='black', style='')
            else:
                gr.attr('node', shape='circle', color='black', style='')
            gr.node(str(i))
            if i in self.init_state:
                gr.edge('qi', str(i), 'start')
        for k1, v1 in self.transition_dict.items():
            for k2, v2 in v1.items():
                if str(v2) != 'ϕ':
                    gr.edge(str(k1), str(k2), str(v2))
        gr.body.append(r'label = "\n\n{0}"'.format(label))
        gr.render(f'{name}', view=True)


    def set_transition_dict(self):
        dict_states = {r: {c: 'ϕ' for c in self.states} for r in self.states}
        for i in self.states:
            for j in self.states:
                indices = [ii for ii, v in enumerate(self.transition_funct[i]) if v == j]
                if len(indices) != 0:
                    valid_indices = [v for v in indices if v < len(self.alphabets)]
                    if valid_indices:
                        dict_states[i][j] = '+'.join([str(self.alphabets[v]) for v in valid_indices])
                    else:
                        dict_states[i][j] = 'ϕ'  # Or handle invalid case here
        self.ds = dict_states
        self.transition_dict = copy.deepcopy(dict_states)


    def get_intermediate_states(self):
        return [state for state in self.states if state not in ([self.init_state] + self.final_states)]

    def simplify_regex(self, regex):
        regex = regex.replace('+ϕ', '').replace('ϕ+', '').replace('(ϕ)', '').replace('()', '')
        # Remove duplicate terms (basic optimization)
        parts = sorted(set(regex.split('+')))
        return '+'.join(parts)

    def toregex(self):
        intermediate_states = self.get_intermediate_states()
        dict_states = self.ds

        for inter in intermediate_states:
            predecessors = [key for key, value in dict_states.items() if value.get(inter, 'ϕ') != 'ϕ' and key != inter]
            successors = [key for key, value in dict_states[inter].items() if value != 'ϕ' and key != inter]
            inter_loop = dict_states[inter].get(inter, 'ϕ') if dict_states[inter].get(inter, 'ϕ') != 'ϕ' else ''

            for i in predecessors:
                for j in successors:
                    new_transition = f"({dict_states[i][inter]})({inter_loop})*({dict_states[inter][j]})"
                    if dict_states[i][j] != 'ϕ':
                        dict_states[i][j] = f"({dict_states[i][j]})+{new_transition}"
                    else:
                        dict_states[i][j] = new_transition
                    dict_states[i][j] = self.simplify_regex(dict_states[i][j])

            dict_states = {r: {c: v for c, v in val.items() if c != inter} for r, val in dict_states.items() if r != inter}

        print(f"Final Transition Dictionary: {dict_states}")

        init_loop = dict_states.get(self.init_state, {}).get(self.init_state, 'ϕ')
        final_expressions = []
        for final_state in self.final_states:
            final_path = dict_states.get(self.init_state, {}).get(final_state, 'ϕ')
            if final_path != 'ϕ':
                final_path = f"({final_path})"
                final_loop = f"({dict_states.get(final_state, {}).get(final_state, 'ϕ')})*" if dict_states.get(final_state, {}).get(final_state, 'ϕ') != 'ϕ' else ''
                final_expressions.append(f"{init_loop}{final_path}{final_loop}")

        return self.simplify_regex('+'.join(final_expressions))


def main():
    states = input('Enter the states in your DFA (space-separated): ').split()
    alphabets = input('Enter the alphabets (space-separated): ').split()
    init_state = input('Enter initial state: ')
    final_states = input('Enter the final states (space-separated): ').split()
    print('Define the transition function:')
    transition_matrix = [input(f'Transitions from state {state} (space-separated states): ').split() for state in states]
    transition_funct = dict(zip(states, transition_matrix))

    dfa = DFA(states, alphabets, init_state, final_states, transition_funct)
    dfa.draw_graph('DFA Graph', 'dfa_graph')
    regex = dfa.toregex()
    print(f"Regular Expression: {regex}")    


if __name__ == '__main__':
    main()
