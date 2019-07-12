####tavern 关键字使用说明

**setup**

`setup` 关键字定义了当前用例的所依赖的相关用例，主要是为了准备执行用例前所依赖的数据如登录信息等。在当前用例执行前会运行该 `setup` 测试用例，可以选择是否保留测试用例执行的数据，以便供其他用例共享。

`setup` 关键字可实现以下功能：
- 默认保留测试用例执行的数据
- 如果不保留测试用例执行的数据，则表示这份数据只作用于当前用例，不会影响其他用例

使用方法如下：

```yaml
setup:
  - [path string] : 资源地址
  - path: [path string] 资源地址
    saved: [bool] 是否保存数据供其他测试用例使用
```

**marks**

`marks` 关键字可实现以下功能：

- 从命令行中选择要运行的标记测试的子集
- 根据条件跳过某些测试
- 将测试标记为暂时预期失败，以便稍后修复

以下是几种 `mark`：

`skip`

要始终跳过测试，只需使用`skip`标记：

```yaml
marks:
  - skip (可以通过将skip关键字插入 stage 来跳过单个 stage )

stages:
  - name: Get info
    skip: True
    request:
      url: "{host}/get-info-slow"
      method: GET
    response:
      status_code: 200
      body:
        n_users: 2048
        n_queries: 10000
```

`skipif`

有时需要跳过一些测试，如下：

```yaml
name: Get server info from slow endpoint

marks:
  - slow
  - skipif: "'slow-example.com' in '{host}'"

stages:
  - name: Get info
    request:
      url: "{host}/get-info-slow"
      method: GET
    response:
      status_code: 200
      body:
        n_users: 2048
        n_queries: 10000
```

`xfail`

如果您希望测试由于某种原因而失败，例如如果测试暂时中断，则可以将测试标记为 `xfail`。

```yaml
name: Get user middle name from endpoint on v2 api fails

marks:
  - xfail

stages:
  - name: Try to get from v2 api
    request:
      url: "{host}/api/v2/users/{user_id}/get-middle-name"
      method: GET
    response:
      status_code: 200
      body:
        middle_name: Jimmy
```

`parametrize`

很多时候您希望确保您的 API 在许多给定输入中正常运行。这是参数化标记的来源：

```yaml
name: 输入关键字，全局搜索项目

marks:
  - parametrize:
      key: type
      vals:
        - project
        - task
        - resource

stages:
  - id: search
    name: 全局搜索项目
    request:
      url: '{project.server}/team/{team.uuid}/search'
      method: GET
      headers:
        Ones-User-Id: '{user.uuid}'
        Ones-Auth-Token: '{user.token}'
      params:
        q: 'search'
        types: '{type}'
        start: 0
        limit: 50
    response:
      status_code: 200
```

该测试用例将作为 3 个单独的测试用例运行 4 次，type 每次运行时从 vals 提供的参数值获取到。

注意：parameterize 处理的顺序在 skipif 之后，所以 skipif 不能依赖 parameterize 生成的数据

多个标记可用于参数化多个值：

```yaml
name: Test post a new fruit

marks:
  - parametrize:
      key: fruit
      vals:
        - apple
        - orange
        - pear
  - parametrize:
      key: edible
      vals:
        - rotten
        - fresh
        - unripe

stages:
  - name: Create a new fruit entry
    request:
      url: "{host}/fruit"
      method: POST
      json:
        fruit_type: "{edible} {fruit}"
    response:
      status_code: 201
```

这将导致运行 9 个测试：
- rotten apple
- rotten orange
- rotten pear
- fresh apple
- fresh orange
- fresh pear
- unripe apple
- unripe orange
- unripe pear

如果需要参数化多个 key，但是又不想生成多个可能的组合，那么需要给 key 赋一个 list，vals 也需要设置跟 key 一样长度的数组，表示对应顺序指定的 key 的 value。这样生成的测试用例的数量就取决于 vals 的长度，如下：


```yaml
name: Test post a new fruit

marks:
- parametrize:
  key: 
	- fruit
	- edible
  vals:
    - [rotten, apple]
    - [fresh, orange]
    - [unripe, pear]
    
stages:
- name: Create a new fruit entry
  request:
  url: "{host}/fruit"
  method: POST
  json:
  fruit_type: "{edible} {fruit}"
  response:
  status_code: 201
```
这样写，将仅生成那 3 个测试用例。
  
当然，也可以指定多组 key - vals，请看以下用例：

```yaml

name: Test post a new fruit and price

marks:
- parametrize:
  key: 
   - fruit 
   - edible
  vals: 
   - [rotten, apple] 
   - [fresh, orange]
   - [unripe, pear]
- parametrize:
  key: price
  vals: 
   - expensive
   - cheap

stages:
- name: Create a new fruit entry
  request:
  url: "{host}/fruit"
  method: POST
  json:
  fruit_type: "{price} {edible} {fruit}"
  response:
  status_code: 201
```
  这将导致 6 个测试：
- expensive rotten apple
- expensive fresh orange
- expensive unripe pear
- cheap rotten apple
- cheap fresh orange
- cheap unripe pear

`usefixtures`

`yield` 任何 `fixture` 的返回（或 ed）值将可用于格式化，使用 `fixture` 名称。

如何使用：

`conftest.py`

```python
import os
import yaml
import pytest

@pytest.fixture(name="clear_tmp_dir")
def clear_tmp_dir():
    yield
    if os.path.exists('./tmp'):
        os.system('rm -rf ./tmp')
```

```yaml
name: 修改任务描述，上传图片

includes:
  - !include /cases/project/resource/qiniu/stage_up_qbox_200.yaml

marks:
  - usefixtures:
    - create_tmp_file

stages:
  - ref: task_file_upload
```

上面的示例将在运行测试用例后，执行 create_tmp_file 函数

`usefixtures` 需要一个 `fixture` 函数名称列表，然后由 Pytest 加载 

注意：
`fixture`的作用于测试用例，而不是每个`stage`。另外，tavern 对 pytest 的 fixtures 有一些局限性的支持，需要使用 usefixtures 这个 mark。通过 return 或者 yield 来返回任何 fixture 。使用 fixture 需要指定 fixture 的名称，会在字符串格式化的时候起作用

**stages**
- `times` 关键字作用于测试用例单个 stage 中，表示运行 stage次数，常用于批量造数据

下面的用例，表示运行 10 次  stage: tasks_add2

```yaml
name: 新建 10 任务

includes:
  - !include /cases/project/auth/login/stage_login_200.yaml

stages:
  - ref: login
  - id: tasks_add2
    times: 10
    name: 创建任务
    request:
      url: '{project.server}/team/{team.uuid}/tasks/add2'
      method: POST
      headers:
        content-type: application/json
        Ones-User-Id: '{user.uuid}'
        Ones-Auth-Token: '{user.token}'
      json:
        tasks:
          - uuid: AAAAAAAA
            summary: 'task name'
            project_uuid: '{project_uuid}'
            issue_type_uuid: '{issue_type_config.0}'
            owner: '{user.uuid}'
            assign: '{user.uuid}'
            desc_rich: ''
            parent_uuid: ''
            priority: '{priority.0.uuid}'
    response:
      status_code: 200
```