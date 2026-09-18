import gc
import pytest

# Disable cyclic GC during test runs to avoid Python 3.14 alpha GC bug in PRoot
gc.disable()


@pytest.fixture(autouse=True)
async def cleanup_resources():
    """Per-test fixture."""
    yield
