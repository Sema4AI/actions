<!-- markdownlint-disable -->

# API Overview

## Modules

- [`sema4ai.common`](./sema4ai.common.md#module-sema4aicommon): sema4ai-common is a library for common utilities to be shared across sema4ai
- [`sema4ai.common.callback`](./sema4ai.common.callback.md#module-sema4aicommoncallback)
- [`sema4ai.common.monitor`](./sema4ai.common.monitor.md#module-sema4aicommonmonitor)
- [`sema4ai.common.null`](./sema4ai.common.null.md#module-sema4aicommonnull)
- [`sema4ai.common.process`](./sema4ai.common.process.md#module-sema4aicommonprocess): Module with utilities for working with processes.
- [`sema4ai.common.protocols`](./sema4ai.common.protocols.md#module-sema4aicommonprotocols)
- [`sema4ai.common.run_in_thread`](./sema4ai.common.run_in_thread.md#module-sema4aicommonrun_in_thread)
- [`sema4ai.common.system_mutex`](./sema4ai.common.system_mutex.md#module-sema4aicommonsystem_mutex): To use, create a SystemMutex, check if it was acquired (get_mutex_aquired()) and if acquired the
- [`sema4ai.common.tools`](./sema4ai.common.tools.md#module-sema4aicommontools)
- [`sema4ai.common.wait_for`](./sema4ai.common.wait_for.md#module-sema4aicommonwait_for)

## Classes

- [`callback.Callback`](./sema4ai.common.callback.md#class-callback): A helper class to register callbacks and call them when notified.
- [`callback.OnExitContextManager`](./sema4ai.common.callback.md#class-onexitcontextmanager)
- [`monitor.Monitor`](./sema4ai.common.monitor.md#class-monitor)
- [`null.Null`](./sema4ai.common.null.md#class-null): Null object pattern.
- [`process.IProgressReporter`](./sema4ai.common.process.md#class-iprogressreporter)
- [`process.Process`](./sema4ai.common.process.md#class-process)
- [`process.ProcessResultStatus`](./sema4ai.common.process.md#class-processresultstatus)
- [`process.ProcessRunResult`](./sema4ai.common.process.md#class-processrunresult): ProcessRunResult(stdout: 'str', stderr: 'str', returncode: 'int', status: 'ProcessResultStatus')
- [`protocols.ActionResult`](./sema4ai.common.protocols.md#class-actionresult)
- [`protocols.ActionResultDict`](./sema4ai.common.protocols.md#class-actionresultdict)
- [`protocols.ICancelMonitorListener`](./sema4ai.common.protocols.md#class-icancelmonitorlistener)
- [`protocols.IMonitor`](./sema4ai.common.protocols.md#class-imonitor)
- [`protocols.Sentinel`](./sema4ai.common.protocols.md#class-sentinel)
- [`system_mutex.SystemMutex`](./sema4ai.common.system_mutex.md#class-systemmutex)
- [`tools.ActionServerTool`](./sema4ai.common.tools.md#class-actionservertool)
- [`tools.AgentCliTool`](./sema4ai.common.tools.md#class-agentclitool)
- [`tools.BaseTool`](./sema4ai.common.tools.md#class-basetool)
- [`tools.DataServerTool`](./sema4ai.common.tools.md#class-dataservertool)
- [`tools.RccTool`](./sema4ai.common.tools.md#class-rcctool)

## Functions

- [`process.build_python_launch_env`](./sema4ai.common.process.md#function-build_python_launch_env): Args:
- [`process.build_subprocess_kwargs`](./sema4ai.common.process.md#function-build_subprocess_kwargs)
- [`process.check_output_interactive`](./sema4ai.common.process.md#function-check_output_interactive): This has the same API as subprocess.check_output, but allows us to work with
- [`process.is_process_alive`](./sema4ai.common.process.md#function-is_process_alive)
- [`process.kill_process_and_subprocesses`](./sema4ai.common.process.md#function-kill_process_and_subprocesses)
- [`process.launch_and_return_future`](./sema4ai.common.process.md#function-launch_and_return_future): Launches a process and returns a future that can be used to wait for the process to
- [`protocols.check_implements`](./sema4ai.common.protocols.md#function-check_implements): Helper to check if a class implements some protocol.
- [`run_in_thread.run_in_thread`](./sema4ai.common.run_in_thread.md#function-run_in_thread): Runs a given target in a thread returning a Future which can be used to
- [`run_in_thread.run_in_thread_asyncio`](./sema4ai.common.run_in_thread.md#function-run_in_thread_asyncio): Runs a given target in a thread returning an asyncio Future which can be
- [`system_mutex.check_valid_mutex_name`](./sema4ai.common.system_mutex.md#function-check_valid_mutex_name)
- [`system_mutex.generate_mutex_name`](./sema4ai.common.system_mutex.md#function-generate_mutex_name): A mutex name must be a valid filesystem path, so, this generates a hash
- [`system_mutex.get_tid`](./sema4ai.common.system_mutex.md#function-get_tid)
- [`system_mutex.timed_acquire_mutex`](./sema4ai.common.system_mutex.md#function-timed_acquire_mutex): Acquires the mutex given its name, a number of attempts and a time to sleep between each attempt.
- [`wait_for.wait_for_condition`](./sema4ai.common.wait_for.md#function-wait_for_condition): Note: wait_for_non_error_condition or wait_for_expected_func_return are usually a better APIs
- [`wait_for.wait_for_expected_func_return`](./sema4ai.common.wait_for.md#function-wait_for_expected_func_return): Args:
- [`wait_for.wait_for_non_error_condition`](./sema4ai.common.wait_for.md#function-wait_for_non_error_condition): Args:
