"""KnowledgeAgent: builds the learner model every other agent conditions on."""
from .metrics import tracked


def make_nodes(ctx):
    @tracked('knowledge')
    def profile_learner(state):
        profile = ctx.knowledge.profile(state['user_id'])
        return {'profile': profile}

    return {'profile_learner': profile_learner}
