const { execSync } = require('child_process');
const path = require('path');

exports.default = async function (context) {
  // 只在 macOS 下执行
  if (context.electronPlatformName !== 'darwin') return;

  const appPath = path.join(context.appOutDir, `${context.packager.appInfo.productName}.app`);
  console.log(`[afterPack] 处理 macOS 应用: ${appPath}`);

  try {
    // 1. 移除所有 quarantine 属性
    console.log('[afterPack] 移除 quarantine 属性...');
    execSync(`xattr -cr "${appPath}"`, { stdio: 'inherit' });

    // 2. 做 ad-hoc 签名（用 - 表示自签名）
    console.log('[afterPack] 执行 ad-hoc 签名...');
    execSync(`codesign --force --deep --sign - "${appPath}"`, { stdio: 'inherit' });

    console.log('[afterPack] 处理完成');
  } catch (err) {
    console.error('[afterPack] 处理出错:', err.message);
    // 不阻止打包流程，继续
  }
};
