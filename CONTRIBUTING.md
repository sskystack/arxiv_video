# 贡献指南

感谢您对 ArXiv Video Downloader 项目的关注！我们欢迎所有形式的贡献。

## 🤝 如何贡献

### 报告问题 (Issues)

如果您发现了bug或有新功能建议，请：

1. **搜索现有Issues** - 确保问题未被报告过
2. **使用Issue模板** - 选择合适的模板填写
3. **提供详细信息** - 包括错误信息、操作系统、Python版本等
4. **复现步骤** - 详细描述如何重现问题

### 提交代码 (Pull Requests)

#### 开发环境设置

```bash
# 1. Fork项目到你的GitHub账号
# 2. 克隆你的fork
git clone https://github.com/YOUR_USERNAME/arxiv_video.git
cd arxiv_video

# 3. 添加上游仓库
git remote add upstream https://github.com/sskystack/arxiv_video.git

# 4. 创建开发环境
python -m venv dev_env
source dev_env/bin/activate  # Windows: dev_env\Scripts\activate

# 5. 安装开发依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 如果存在

# 6. 安装pre-commit钩子
pre-commit install
```

#### 开发流程

1. **创建功能分支**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **编写代码**
   - 遵循项目代码风格
   - 添加必要的注释和文档
   - 编写单元测试

3. **测试代码**
   ```bash
   # 运行测试
   python -m pytest tests/
   
   # 代码格式检查
   black .
   flake8 .
   
   # 类型检查
   mypy .
   ```

4. **提交更改**
   ```bash
   git add .
   git commit -m "feat: 添加新功能的简要描述"
   ```

5. **推送到GitHub**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **创建Pull Request**
   - 填写PR模板
   - 描述更改内容
   - 关联相关Issues

## 📝 代码规范

### Python代码风格

- 使用 [Black](https://black.readthedocs.io/) 进行代码格式化
- 遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/) 规范
- 使用 [Type Hints](https://docs.python.org/3/library/typing.html)

### 提交信息规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

```
<类型>[可选的作用域]: <描述>

[可选的正文]

[可选的脚注]
```

**类型说明：**
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 重构代码
- `test`: 添加或修改测试
- `chore`: 构建或辅助工具的变动

**示例：**
```
feat(downloader): 添加断点续传功能

支持在下载中断后从断点处继续下载，提高用户体验。

Closes #123
```

### 文档规范

- 使用中文编写文档
- 函数和类需要完整的docstring
- README和重要文档需要同时提供中英文版本

## 🧪 测试要求

### 单元测试

- 新功能必须包含单元测试
- 测试覆盖率不低于80%
- 使用pytest框架

### 集成测试

- 关键功能需要端到端测试
- 测试不同操作系统和Python版本的兼容性

## 📋 PR检查清单

在提交PR前，请确保：

- [ ] 代码通过所有测试
- [ ] 新功能包含测试用例
- [ ] 更新了相关文档
- [ ] 遵循代码规范
- [ ] 提交信息符合规范
- [ ] 没有引入安全漏洞
- [ ] 向后兼容（除非是破坏性更改）

## 🏷️ 发布流程

1. **版本号规范** - 使用 [Semantic Versioning](https://semver.org/)
2. **变更日志** - 更新 CHANGELOG.md
3. **标签发布** - 创建对应的Git标签
4. **发布说明** - 在GitHub Releases中发布

## 📞 联系方式

- **GitHub Issues**: 用于bug报告和功能请求
- **Discussions**: 用于一般讨论和问答
- **Email**: 项目维护者邮箱

## 🎉 贡献者

感谢所有为本项目做出贡献的开发者！

<!-- 这里会自动显示贡献者头像 -->
![Contributors](https://contributors-img.web.app/image?repo=sskystack/arxiv_video)

## 📄 许可证

贡献代码即表示您同意将代码以 MIT 许可证发布。
