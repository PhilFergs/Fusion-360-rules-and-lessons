from philsfusion.commands.design import context, logger


def test_logger_writes_only_to_configured_data_folder(tmp_path):
    path = tmp_path / "logs" / "design-tools.log"
    logger.configure(path)

    logger.log("started")

    assert path.read_text(encoding="utf-8").endswith("started\n")
    assert list(tmp_path.rglob("*.log")) == [path]


def test_context_init_clears_stale_handler_references():
    context.add_handler(object())
    context.init(object(), object())

    assert context.handler_count() == 0


def test_context_clear_handlers_is_idempotent():
    context.add_handler(object())

    context.clear_handlers()
    context.clear_handlers()

    assert context.handler_count() == 0
