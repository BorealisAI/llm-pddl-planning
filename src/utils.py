# Copyright (c) 2024-present, Royal Bank of Canada.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.
#

import logging
import os
import uuid
import multiprocessing


def postprocess(x):
    return x.strip()


def get_random_temp_file_name(suffix='txt'):
    return os.path.join('/tmp', f"{str(uuid.uuid4())[:8]}.{suffix}")


def read_and_remove_file(f_name):
    with open(f_name, 'r') as f:
        x = f.read()
    os.remove(f_name)
    return x


def as_file(x, suffix='txt'):
    f_name = get_random_temp_file_name(suffix=suffix)
    with open(f_name, 'w') as f:
        f.write(x)
    return f_name


def wrap_code(code, lang):
    return f"```{lang}\n" + code + "\n```"


def extract_code(text, lang):
    """
    Extract code from a text that is wrapped in a code block. All code blocks are extracted and concatenated.
    """
    code_start = f"```{lang}"
    code_end = "```"
    if code_start not in text:
        raise ValueError(f"Could not find code in text:\n{text}")
    else:
        # extract all code blocks
        code_blocks = []
        for code_block in text.split(code_start)[1:]:
            code_blocks.append(code_block.split(code_end)[0].strip())
        return "\n".join(code_blocks)


def safe_function_execute(func, *args):
    def _exec_func(q, f, *ar):
        res = f(*ar)
        q.put(res)

    # execute func, return the result. In case of exception, return None
    # create a new process for it
    queue = multiprocessing.Queue()
    process = multiprocessing.Process(target=_exec_func, args=(queue, func, *args))
    process.start()
    # Wait for the process to finish
    process.join()

    # Retrieve the result from the queue
    try:
        result = queue.get(timeout=1.0)
    except Exception as e:
        logging.warning(f"Exception while executing the function {func}.")
        result = None
    return result


def cached_func(func, cache):
    def _cached_func(*args):
        if args not in cache:
            cache[args] = func(*args)
        return cache[args]

    return _cached_func


def get_function_from_code(fn_code, fn_name):
    exec(fn_code)
    return locals()[fn_name]


def mean(x):
    return sum(x) / len(x)


def harmonic_mean(a, b):
    try:
        return 2 * a * b / (a + b)
    except ZeroDivisionError:
        return 0.0
