import pytest

from core.state.state import State, StateManager
from core.state.transitions import Transition, on_success, on_failure, state_equals
from core.state.builder import SiteStateBuilder
from core.state.actions import Action, ActionResult
from core.state.persistence import InMemoryPersister

from core.ui.state import ComponentConfig, ComponentType, VisibilityCondition
from core.ui.state.config import ComponentLibrary


def test_state_update_is_immutable_and_increments_sequence():
    s1 = State({"a": 1})
    s2 = s1.update(a=2, b=3)

    assert s1.get("a") == 1
    assert "b" not in s1

    assert s2.get("a") == 2
    assert s2.get("b") == 3
    assert s2.sequence_id == s1.sequence_id + 1


def test_state_private_keys_hidden_in_keys_and_get_all():
    s = State({"visible": 1, "__secret": 2})
    assert "visible" in s.keys()
    assert "__secret" not in s.keys()
    assert s.get_all() == {"visible": 1}


def test_state_append_and_merge_validation():
    s = State({"items": [1]})
    s2 = s.append(items=2)
    assert s.get("items") == [1]
    assert s2.get("items") == [1, 2]

    with pytest.raises(ValueError):
        State({"x": 1}).append(x=2)

    s3 = State({"cfg": {"a": 1}}).merge("cfg", {"b": 2})
    assert s3.get("cfg") == {"a": 1, "b": 2}

    with pytest.raises(ValueError):
        State({"cfg": 123}).merge("cfg", {"b": 2})


def test_state_subset_and_wipe():
    s = State({"a": 1, "b": 2, "__p": 3})
    sub = s.subset(["a", "__p"])
    assert sub.get_all() == {"a": 1}

    kept = s.wipe(keep=["a"])
    assert kept.get_all() == {"a": 1}
    assert kept.get("__p") == 3

    deleted = s.wipe(delete=["b"])
    assert deleted.get_all() == {"a": 1}

    with pytest.raises(ValueError):
        s.wipe(keep=["a"], delete=["b"])


def test_state_serialize_roundtrip():
    s = State({"a": {"b": [1, 2]}})
    payload = s.serialize()
    s2 = State.deserialize(payload)
    assert s2.get("a") == {"b": [1, 2]}
    assert s2.sequence_id == s.sequence_id


def test_state_manager_history_and_rollback():
    mgr = StateManager(State({"a": 1}))
    mgr.update(mgr.current.update(a=2))
    mgr.update(mgr.current.update(a=3))

    assert mgr.current.get("a") == 3
    prev = mgr.rollback(steps=1)
    assert prev.get("a") == 2

    at0 = mgr.get_at_sequence(0)
    assert at0 is not None
    assert at0.get("a") == 1


@pytest.mark.asyncio
async def test_transition_default_and_conditional():
    t_default = Transition(target="next")
    assert await t_default.should_transition(State(), result=None)

    def cond_ok(state, result):
        return True

    def cond_raises(state, result):
        raise RuntimeError("boom")

    assert await Transition(target="x", condition=cond_ok).should_transition(State(), None)
    assert not await Transition(target="x", condition=cond_raises).should_transition(State(), None)


@pytest.mark.asyncio
async def test_builder_executes_action_and_transitions():
    class SetFlag(Action):
        def __init__(self):
            super().__init__(name="set_flag", reads=[], writes=["flag"])

        async def run(self, state: State, context=None, **inputs) -> ActionResult:
            return ActionResult(success=True, data={"flag": True}, message="ok")

    class CheckFlag(Action):
        def __init__(self):
            super().__init__(name="check_flag", reads=["flag"], writes=[])

        async def run(self, state: State, context=None, **inputs) -> ActionResult:
            return ActionResult(success=bool(state.get("flag")))

    app = (
        SiteStateBuilder()
        .with_actions(SetFlag(), CheckFlag())
        .with_transitions(("set_flag", "check_flag", on_success))
        .with_entrypoint("set_flag")
        .build()
    )

    action_name, result, new_state = await app.step()
    assert new_state.get("flag") is True
    assert action_name == "check_flag"

    action_name2, result2, _ = await app.step()
    assert action_name2 == "check_flag"
    assert result2.success is True


@pytest.mark.asyncio
async def test_persister_in_memory_partition_key_and_sequence_match():
    p = InMemoryPersister()
    s = State({"a": 1})

    ok = await p.save("app", s, partition_key="draft")
    assert ok is True

    loaded = await p.load("app", partition_key="draft")
    assert loaded is not None
    assert loaded.get("a") == 1

    # sequence_id mismatch should return None
    assert await p.load("app", partition_key="draft", sequence_id=999) is None

    ids = await p.list_app_ids(partition_key="draft")
    assert "app" in ids

    deleted = await p.delete("app", partition_key="draft")
    assert deleted is True
    assert await p.load("app", partition_key="draft") is None


def test_component_config_visibility_rules_and_roundtrip():
    c = ComponentConfig(
        id="c1",
        type=ComponentType.CTA,
        name="CTA",
        visibility=VisibilityCondition.AUTHENTICATED,
    )
    assert c.should_render(user=None) is False
    assert c.should_render(user={"id": 1}) is True

    c2 = ComponentConfig(
        id="c2",
        type=ComponentType.CTA,
        name="CTA",
        visibility=VisibilityCondition.NOT_AUTHENTICATED,
    )
    assert c2.should_render(user=None) is True
    assert c2.should_render(user={"id": 1}) is False

    c3 = ComponentConfig(
        id="c3",
        type=ComponentType.CTA,
        name="CTA",
        visibility=VisibilityCondition.IS_MEMBER,
        visibility_params={"site_id": "main"},
    )
    assert c3.should_render(user=None) is False
    assert c3.should_render(user={"member_sites": ["main"]}) is True
    assert c3.should_render(user={"member_sites": []}) is False

    c4 = ComponentConfig(
        id="c4",
        type=ComponentType.NAVIGATION,
        name="Nav",
        visibility=VisibilityCondition.HAS_ROLE,
        visibility_params={"role": "admin"},
    )
    assert c4.should_render(user=None) is False
    assert c4.should_render(user={"roles": ["admin"]}) is True
    assert c4.should_render(user={"roles": ["user"]}) is False

    d = c4.to_dict()
    c4b = ComponentConfig.from_dict(d)
    assert c4b.id == c4.id
    assert c4b.type == c4.type
    assert c4b.visibility == c4.visibility
    assert c4b.visibility_params == c4.visibility_params


def test_component_library_templates_return_component_config():
    lib = ComponentLibrary()
    signup = lib.create_signup_cta()
    assert isinstance(signup, ComponentConfig)
    assert signup.visibility == VisibilityCondition.NOT_MEMBER

    admin_nav = lib.create_admin_only_nav()
    assert admin_nav.visibility == VisibilityCondition.HAS_ROLE
    assert admin_nav.visibility_params["role"] == "admin"
