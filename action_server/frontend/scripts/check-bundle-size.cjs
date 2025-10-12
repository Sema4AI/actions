const fs = require('fs');
const path = require('path');

const dist = path.join(__dirname, '..', 'dist');
if (!fs.existsSync(dist)) {
  console.error('dist directory not found. Run build first.');
  process.exit(2);
}

function sizeOf(dir) {
  const files = fs.readdirSync(dir, { withFileTypes: true });
  let total = 0;
  for (const f of files) {
    const p = path.join(dir, f.name);
    if (f.isDirectory()) total += sizeOf(p);
    else total += fs.statSync(p).size;
  }
  return total;
}

const total = sizeOf(dist);
// Compare to 350KB
const threshold = 350 * 1024;
console.log(`Bundle size: ${(total / 1024).toFixed(2)} KB`);
if (total > threshold) {
  console.error(`Bundle exceeds threshold of ${(threshold / 1024).toFixed(2)} KB`);
  process.exit(1);
}
process.exit(0);
