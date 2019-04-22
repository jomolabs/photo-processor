class BehavioredMock(object):
    def __init__(self, behaviors = {}):
        self.behaviors = behaviors

    def get_has(self, behavior_type, behavior):
        return behavior_type in self.behaviors and self.behaviors[behavior_type] == behavior

    def has_throw_for_type(self, behavior_type):
        return self.get_has(behavior_type, 'throw')

    def has_yield_list(self, behavior_type):
        return behavior_type in self.behaviors and 'yield' in self.behaviors[behavior_type] and isinstance(self.behaviors[behavior_type]['yield'], type([]))

    def get_yield_list(self, behavior_type):
        return self.behaviors[behavior_type]['yield']

    def has_response_list(self, behavior_type):
        return behavior_type in self.behaviors and 'response' in self.behaviors[behavior_type] and isinstance(self.behaviors[behavior_type]['response'], type([]))

    def get_response_list(self, behavior_type):
        return self.behaviors[behavior_type]['response']
