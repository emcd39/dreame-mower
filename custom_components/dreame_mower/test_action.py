"""Test service for trying different siid/aiid combinations.

This service allows testing different action identifiers without
modifying const.py. Add this to services.yaml for testing.
"""

SERVICE_TEST_ACTION = "test_action"
SERVICE_SCHEMA_TEST_ACTION = vol.Schema(
    {
        vol.Required("entity_id"): cv.entity_id,
        vol.Required("siid"): vol.Coerce(int),
        vol.Required("aiid"): vol.Coerce(int),
        vol.Optional("params", default=[]): list,
    }
)


async def async_handle_test_action(
    hass: HomeAssistant,
    entity: DreameMowerEntity,
    siid: int,
    aiid: int,
    params: list = None,
) -> None:
    """Handle test action service call."""
    from ..dreame.const import ActionIdentifier

    _LOGGER.info(f"Testing action: siid={siid}, aiid={aiid}, params={params}")

    # Create a temporary ActionIdentifier
    test_action = ActionIdentifier(siid=siid, aiid=aiid, name=f"test_{siid}_{aiid}")

    # Execute the action
    try:
        result = await asyncio.get_event_loop().run_in_executor(
            None, lambda: entity.coordinator.device._cloud_device.execute_action(test_action)
        )

        if result:
            _LOGGER.info(f"✓ Action succeeded! siid={siid}, aiid={aiid}")
            hass.components.persistent_notification.async_create(
                f"Action succeeded!\n\nsiid: {siid}\naiid: {aiid}\nparams: {params}\n\nAdd this to const.py:\nHOLD_ACTION_NAME = ActionIdentifier(siid={siid}, aiid={aiid}, name=\"action_name\")",
                title="Dreame Mower Test",
                notification_id="dreame_test_action",
            )
        else:
            _LOGGER.warning(f"✗ Action failed: siid={siid}, aiid={aiid}")
            hass.components.persistent_notification.async_create(
                f"Action failed!\n\nsiid: {siid}\naiid: {aiid}\nparams: {params}\n\nTry different siid/aiid values.",
                title="Dreame Mower Test",
                notification_id="dreame_test_action",
            )
    except Exception as ex:
        _LOGGER.error(f"Exception testing action: {ex}")
        hass.components.persistent_notification.async_create(
            f"Exception!\n\nsiid: {siid}\naiid: {aiid}\nerror: {ex}",
            title="Dreame Mower Test",
            notification_id="dreame_test_action",
        )
