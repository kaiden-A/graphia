import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

const root = process.cwd();
const isWindows = process.platform === "win32";

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: root,
    stdio: "inherit",
    ...options,
  });
  if (result.error) {
    console.error(result.error.message);
  }
  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }
}

function copyIfMissing(source, target) {
  if (fs.existsSync(target)) return;
  if (!fs.existsSync(source)) return;
  fs.copyFileSync(source, target);
  console.log(`created ${target}`);
}

function patchWindowsVenv() {
  const venvPython = path.join(root, "server", ".venv", "Scripts", "python.exe");
  if (!fs.existsSync(venvPython)) {
    run("uv", ["venv", "--python", "3.12", "server/.venv"]);
  }

  const found = spawnSync("uv", ["python", "find", "3.12"], {
    cwd: root,
    encoding: "utf8",
  });
  if (found.status !== 0) return;

  const basePython = found.stdout.trim();
  const baseDir = path.dirname(basePython);
  const scripts = path.join(root, "server", ".venv", "Scripts");

  const files = fs.readdirSync(baseDir);
  const pythonDll = files.find(
    (name) => /^python3\d+\.dll$/i.test(name) && name.toLowerCase() !== "python3.dll",
  );

  const copies = ["python.exe", "python3.dll", "vcruntime140.dll", "vcruntime140_1.dll"];
  if (pythonDll) copies.push(pythonDll);

  for (const file of copies) {
    const source = path.join(baseDir, file);
    if (!fs.existsSync(source)) continue;
    fs.copyFileSync(source, path.join(scripts, file));
  }
}

copyIfMissing(path.join(root, "server", ".env.example"), path.join(root, "server", ".env"));
copyIfMissing(
  path.join(root, "client", ".env.example"),
  path.join(root, "client", ".env.local"),
);

if (isWindows) {
  patchWindowsVenv();
}

run("uv", ["sync", "--directory", "server", "--group", "processor"]);
if (isWindows) {
  run("cmd.exe", ["/c", "npm", "--prefix", "client", "install"]);
} else {
  run("npm", ["--prefix", "client", "install"]);
}

console.log("\nSetup complete.");
console.log("Fill in server/.env, then run: npm run dev");
