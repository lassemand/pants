# Copyright 2022 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import annotations

from dataclasses import dataclass

from pants.backend.rust.lint.rustfmt import skip_field
from pants.backend.rust.lint.rustfmt.skip_field import SkipRustfmtField
from pants.backend.rust.lint.rustfmt.subsystem import RustfmtSubsystem
from pants.backend.rust.target_types import RustCrateSourcesField
from pants.backend.rust.util_rules.toolchains import RustToolchainProcess
from pants.core.goals.fmt import FmtRequest, FmtResult
from pants.engine.internals.selectors import Get
from pants.engine.process import ProcessResult
from pants.engine.rules import collect_rules, rule
from pants.engine.target import FieldSet, Target
from pants.util.logging import LogLevel
from pants.util.strutil import pluralize


@dataclass(frozen=True)
class RustfmtFieldSet(FieldSet):
    required_fields = (RustCrateSourcesField,)

    sources: RustCrateSourcesField

    @classmethod
    def opt_out(cls, tgt: Target) -> bool:
        return tgt.get(SkipRustfmtField).value


class RustfmtRequest(FmtRequest):
    field_set_type = RustfmtFieldSet
    name = RustfmtSubsystem.options_scope


@rule(desc="Format with rustfmt")
async def rustfmt_fmt(request: RustfmtRequest.Batch, rustfmt: RustfmtSubsystem) -> FmtResult:
    files = [f for f in request.snapshot.files if f.endswith(".rs")]  # filter out Cargo.toml
    result = await Get(
        ProcessResult,
        RustToolchainProcess(
            binary="rustfmt",
            args=files,
            input_digest=request.snapshot.digest,
            output_files=request.snapshot.files,
            description=f"Run rustfmt on {pluralize(len(files), 'file')}.",
            level=LogLevel.DEBUG,
        ),
    )
    return await FmtResult.create(request, result)


def rules():
    return [
        *collect_rules(),
        *skip_field.rules(),
        *RustfmtRequest.rules(),
    ]
