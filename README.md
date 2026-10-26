# TriCompile
**Author: Swayam Shakya**

A retro code laboratory for learning how programs execute. Write simple commands, inspect stack instructions, step through variables, or run Python, JavaScript, C and C++ with installed local toolchains.

## Start
Requires Python 3.10 or newer. The application uses only Python's standard library.

```sh
python server.py
```

Open **http://127.0.0.1:8765**. On some systems use `python3` instead of `python`. Stop the server with Ctrl+C. Alternatively open `TriCompile.ipynb` in Jupyter and run its cells. The notebook uses the same compiler and starts the same interface; do not start both servers simultaneously.

`index.html` is the main interface. It sends requests to the local Python server, which imports the compiler. Browsers cannot execute a Python notebook directly. GitHub Pages can display the interface but cannot run the Python backend. Run the downloaded project locally for execution.

## Supported languages
| Mode | Features | Dependency |
| --- | --- | --- |
| Beginner | set, show, if/else, while/end | Python |
| TriCompile high-level | let, print, if/else, while/end | Python |
| VM assembly | stack operations, variables, jumps | Python |
| VM bytecode | import hex, inspect hex/binary, execute | Python |
| Python | execution, stdin, syntax checking | current Python |
| JavaScript | execution, stdin, syntax checking | Node.js on PATH |
| C | compilation, execution, stdin, diagnostics | gcc on PATH |
| C++ | compilation, execution, stdin, diagnostics | g++ on PATH |

Use your platform's Python/Node installers and GCC toolchain. Windows can use a MinGW-w64 GCC installation; macOS requires a GCC-compatible compiler command on PATH. Availability is detected at startup. Java, Rust, C#, package installation and multi-file projects are not implemented.

## Try it
```text
set count to 1
while count <= 5
  show count
  set count to count + 1
end
```
Run prints 1 through 5. Compile shows instructions without running. Step executes one additional VM instruction, with the next instruction highlighted. Reset debug starts again. Save/Open handles source text; choose the matching language when opening. Export bytecode saves hex text, which can be opened in VM bytecode mode. Ctrl+Enter runs the program. Native programs accept prefilled standard input, not live interactive input.

Each educational statement occupies one line. Strings use quotes. Arithmetic supports `+ - * // %`, unary minus, and single comparisons `== != < <= > >=`. Variables, integers, strings and booleans are supported; functions, arrays, floating point, chained comparisons and arbitrary English are not. Indentation is cosmetic; close every block with `end`. High-level mode uses `let x = 5;` and `print(x);` with the same block syntax.

Assembly instructions: PUSH, LOAD, STORE, ADD, SUB, MUL, DIV, MOD, EQ, NE, LT, LE, GT, GE, PRINT, JMP, JZ, HALT. JMP/JZ take zero-based numeric addresses; JZ consumes its condition. End assembly programs with HALT. VM bytecode consists of `TCMP`, version byte 1, and UTF-8 JSON instructions. Hex and binary views show those actual serialized bytes. This is an educational VM format, not x86 or ARM machine code.

## Architecture
- `index.html`: responsive editor, output, language chooser, file controls and inspection.
- `server.py`: loopback HTTP API with per-session request token.
- `core.py`: expression parser, statement compiler, validation, serialization and VM.
- `runners.py`: local runtime/compiler adapters.
- `TriCompile.ipynb`: executable walkthrough, assertions and server launcher.
- `tests/test_system.py`: compiler, runtime and HTTP integration tests.

Debug stepping replays a deterministic program to the requested instruction count, so the server stores no debugger sessions. Native languages use their own compilers; their internals are not translated into TriCompile VM instructions. Compile/Check validates native code; native executables are temporary and are not exported.

## Tests
```sh
python -m unittest discover -s tests -v
```
See `TEST_RESULTS.txt` for the actual build-time run. Tests execute real programs in all four installed toolchains, compare outputs, check errors, enforce a timeout, and exercise the local HTTP API. No model training is involved. Testing does not guarantee every program or operating system is error-free. Windows and macOS require local verification.

## Execution boundaries
Run trusted personal code only. Native programs run with your account's permissions: temporary directories and timeouts are **not a security sandbox**. Do not expose this server publicly. Native execution has a 5-second timeout, compilation 15 seconds, and returned output is capped at 64 KiB per stream. Temporary output on disk is not quota-limited; there is no native memory/network/filesystem isolation. VM execution stops at 10,000 instructions. The UI waits for requests to finish; there is no interactive Stop button. Breakpoints, user-defined test suites and native step-debugging are future work.

## License
MIT. See LICENSE.
