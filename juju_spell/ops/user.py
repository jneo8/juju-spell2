"""Ops for user."""
import typing as t

from loguru import logger
from juju.controller import Controller
from juju.user import User
from juju.errors import JujuError

from juju_spell.settings import CtrSettings
from juju_spell.utils import Namespace, ModelFilterMixin
from juju_spell.errors import JujuSpellError
from .base import Ops, ComposeOps
from .controller import ControllerWrapOps


class _AddUserPrecheckOps(Ops):
    async def _run(
        self,
        ctr: Controller,
        username: str,
        ctr_settings: CtrSettings,
        *args: t.Any,
        **kwargs: t.Any,
    ) -> bool:
        if username == ctr_settings.user:
            raise JujuSpellError("User can't manage itself")
        return True


AddUserPrecheckOps = _AddUserPrecheckOps()


class _GrantControllerOps(Ops):
    def get_controller_acl(self, acl: str) -> str:
        """Get corresponding controller acl from input acl."""
        if acl in ["admin", "add-model", "login"]:
            controller_acl = acl
        else:
            controller_acl = "login"
        return controller_acl

    async def _run(
        self,
        ctr: Controller,
        username: str,
        acl: str,
        *args: t.Any,
        **kwargs: t.Any,
    ) -> bool:
        acl = self.get_controller_acl(acl)
        await ctr.grant(username=username, acl=acl)
        return True


GrantControllerOps: Ops = _GrantControllerOps()


class _GrantModelOps(Ops, ModelFilterMixin):
    def get_model_acl(self, acl: str) -> str:
        """Get corresponding model acl from input acl."""
        if acl in ["admin", "read", "write"]:
            model_acl = acl
        elif acl == "superuser":
            model_acl = "admin"
        else:
            model_acl = "read"
        return model_acl

    async def _run(
        self,
        ctr: Controller,
        username: str,
        models: t.List[str],
        acl: str,
        *args: t.Any,
        **kwargs: t.Any,
    ) -> bool:
        acl = self.get_model_acl(acl)
        async for _, model in self.model_async_generator(ctr=ctr, models=models):
            try:
                await ctr.grant_model(username=username, model_uuid=model.uuid, acl=acl)
            except JujuError as err:
                logger.warning(err)
        return True


GrantModelOps = _GrantModelOps()


class _CreateUserOps(Ops):
    async def _run(
        self,
        ctr: Controller,
        username: str,
        password: str,
        display_name: str,
        overwrite: bool,
        *args: t.Any,
        **kwargs: t.Any,
    ) -> bool:
        user: t.Optional[User] = await ctr.get_user(username=username)
        if user is None:
            user = await ctr.add_user(
                username=username,
                password=password,
                display_name=display_name,
            )

        if overwrite:
            await user.set_password()
            logger.info(f"Reset user {username} password")
        return user


CreateUserOps = _CreateUserOps()

EnableUserOps: Ops = ControllerWrapOps(
    name="enable_user", cmd="enable_user", allow_options=["username"]
)

AddUserOps: ComposeOps = ComposeOps(
    [
        AddUserPrecheckOps,
        CreateUserOps,
        EnableUserOps,
        GrantControllerOps,
        GrantModelOps,
    ]
)
