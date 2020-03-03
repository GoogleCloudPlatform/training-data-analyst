local env = std.extVar("__ksonnet/environments");
local params = std.extVar("__ksonnet/params").components.ui;
local k = import "k.libsonnet";

local ui = import "ui.libsonnet";

std.prune(k.core.v1.list.new(ui.parts(params, env)))
