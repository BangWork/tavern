## ONES Tavern 定制化修改

### Validation

validation 和原本的 tavern 框架有了很大的不同

validation 将所有的 block 统一成为了一个通用的 validate block，包含一组 validator
```yml
---
name: test

stages:
  - name: test stage
    request:
      ...
    response:
      validate:
        - eq: ["{body.email}","{request.email}"]
        - leq: ["{body.users}",2]
```

validation 使用 comparators 来做值的校验，同时也支持用 $ext 来支持校验扩展

```yml
---
name: test
stages:
  - name: test stage
    request:
      ...
    response:
      validate:
        - $ext:
          function: module:test
          extra_args:
            - 1
          extra_kwargs:
            a : 1
```
在 validate block 中定义 $ext 第一个参数默认值为 `response`

```python
# module 下 test.py
def test(response,**args,**kwargs):
  assert args[0] == 1
  assert kwargs["a"] == 1
```

定制化后内置的了一组 comparators，每一个 comparators 都有多个别名，方便使用
```python
if comparator in ["eq", "equals", "==", "is"]:
    return "equals"
elif comparator in ["lt", "less_than"]:
    return "less_than"
elif comparator in ["le", "less_than_or_equals"]:
    return "less_than_or_equals"
elif comparator in ["gt", "greater_than"]:
    return "greater_than"
elif comparator in ["ge", "greater_than_or_equals"]:
    return "greater_than_or_equals"
elif comparator in ["ne", "not_equals"]:
    return "not_equals"
elif comparator in ["str_eq", "string_equals"]:
    return "string_equals"
elif comparator in ["len_eq", "length_equals", "count_eq"]:
    return "length_equals"
elif comparator in ["len_gt", "count_gt", "length_greater_than", "count_greater_than"]:
    return "length_greater_than"
elif comparator in ["len_ge", "count_ge", "length_greater_than_or_equals",
                    "count_greater_than_or_equals"]:
    return "length_greater_than_or_equals"
elif comparator in ["len_lt", "count_lt", "length_less_than", "count_less_than"]:
    return "length_less_than"
elif comparator in ["len_le", "count_le", "length_less_than_or_equals",
                    "count_less_than_or_equals"]:
    return "length_less_than_or_equals"
```
上面的 return 指代表真正对应的 comparators 方法，上面的数组则是 comparators 的别名，意思是，可以使用别名来做为 validator 的 key，其中每个函数的作用在 [Extension](#Extension) 章节里会说明

```yml
name: test

stages:
  - name: test stage
    request:
      ...
    response:
      validate:
        - eq: ["{body.email}","{request.email}"]
        - is: ["{body.user.uuid}","bcd"]
        - ==: ["{body.team.uuid}","abc"]
```


### Variables

定制版本对于 variables 的使用做了比较大的提升

variables 的基础写法
```yml
---
name: 
variables:
  a: 1
  b: 2

request:
  json:
    # 当变量的格式为 "{variables}"，前后都没有其他东西的时候，此时，a的变量值类型会使用原始类型，
    # 这里 a 会得到 int 的值
    # 如果 a 是一个 dict，这里 a 也会直接接受 dict 值 
    a : "{a}"
    # 如果是以下的格式，则返回的是一个字符串
    b : "{b}_{a}"
    # 可以使用 $ext 来生成变量的值
    c :
      $ext:
        function: module:function
        extra_args:
          - "{a}"
          - "{b}"
    # 也可以加上类型转换，将结果直接转换成对应的类型，其中类型转换包含了 !int !str !float !bool 四种简单类型
    a: !int "{a}"
```

如果 variables 里的变量名，在当前 stage 的 variables 里找不到，则会 key error 的错误

variables 的信息可以在 console 里的 debug 一栏里找到对应的 log

在 variables.yaml 的很多地方都会可以使用 variables 变量的格式
```yml
# varaibles.yaml
---
name: variables
variables:
  a : 1
  b : 2


# stage.yaml
---
name: presetation
includes:
  - !include variables.yaml
# 在 stage 里定义的 variables 此时使用的变量是从 included 的文件里获取来的或是全局配置里获取到 variables，最终会合并成为当前 stage 所需的所有 variables
varaibles:
  a: "{a}"
  b: "{b}"

# marks 标签可以使用
marks:
  - skipif: "{a} == a"

#request 可以使用
request:
  url: '{a}'
  method: '{a}'
  json:
    $ext: 
      function: module:function

response:
  status_code: 200
  #cookie 可以使用
  cookie: 
    "cookie":{a}
  # validate 可以使用，同时 validate 使用有一些特殊的地方
  validate:
    # 如果 validate 中的元素整个为 $ext 扩展的格式，则此时，function 的第一个参数为 response
    - $ext:
      function: module:function
      extra_args:
        # 否则，与其他的地方变量一至
        - $ext:
          function: module:function
          
  save:
    # save 可以使用 $ext 关键字，如果是 save 的直接子节点，此时 function 的第一个参数为 response
    $ext:
      function: module:function
    key : {body.user.uuid}

```

其中, request 的 可以在 response 里使用
```yml
---
name: yaml
request:
  url: "123"
  method: "234"
  json: 
    a: 111
    b: 222
response:
  save:
    url: "{request.url}"
    a: "{request.json.a}"
```

另外，在 response block 中可以使用 body, headers, redirect_query_params 几个的内容来单独做 variables 的使用

```yml
name: yaml
request:
  url: "123"
response:
  save:
    url: "{body.user.uuid}"
    a: "{headers.context-type}"
    b: "{redirect_query_params.location}"
```

### Extension

tavern 本身的 Extension 非常强大，但是使用有一些不方便的地方。

定制版本的 tavern 做了一些改进，首先在 [Variables](#Variables) 中介绍了任何使用变量的地方都能够使用 $ext 来对获取变量。

在 response 的 validate, save 区块里都会加入了增加了一些特殊逻辑，具体例子可以参考  [Variables](#Variables) 中的例子的注释部分

另外，也让 $ext 支持了 “内置函数” 的概念

```yml
---
name: test
response:
  save:
    key1: 
      $ext:
        # 非内置函数需要声明module
        function: module:a
    key2:
      $ext:
        # 内置函数可以直接使用
        function: random_string
```

目前内置的函数包含:

`random_string`: 生成随机字符串，参数如下
* `length`: 随机字符串的长度，默认值：8
* `prefix`: 前缀，默认值：""
* `has_number`: 随机字符串里是否包含数字，默认值：True
* `has_lowercase`: 随机字符串里是否包含小写字符，默认值: True
* `has_uppercase`: 随机字符串中是否包含大写字符，默认值： True

`uuid`: 生成随机的8位 UUID 字符串，参数如下
* `prefix`: uuid 前缀, 默认值：""

除了以上两个内置方法，所有的 comparators 方法也可以使用 $ext 的方式调用
参数为第一个为 checked_value, 第二个为 expect_value。需要检查的值和期待值。当 checked_value 和 expect_value 不满足比较条件时会报 AssertionError 的错误

`equals`: 比较 checked_value 是否等于 expect_value，这是一个深比较。
```yaml
name: test equal
stages:
  - name: test equal stage
    response:
      validate:
        - eq:
          - "{body}"
          # 具体比较时会变量 body 的所有嵌套结构来做值的验证，只要有一个子节点不正确，都会报错。
          # 如果嵌套的内容是数组，也会对数组的元素进行校验
          - a: a
            b: b
```

同时支持一些 magic value，可以用一些特殊场景的校验。比如:
```yml
---
name: test equal
stages:
  - name: test equal stage
    response:
      validate:
        - eq:
          - "{body.uuid}"
          # 验证 body.uuid 是否存在
          - !anything
```
目前可用的 magic value 包含:
* `anything`: 任意值，通常用于验证是否存在
* `anyint`: 任意整型
* `anyfloat`: 任意浮点型
* `anystr`: 任意字符串
* `anybool`: 任意布尔值

`less_than`: checked_value 是否小于 expected_value

`less_than_or_equals`: checked_value 是否小于等于 expected_value

`greater_than_or_equals`: checked_value 是否大于等于 expected_value

`greater_than`: checked_value 是否大于 expected_value

`not_equals`: checked_value 是否不等于 expected_value

`string_equals`: checked_value 和 expected_value 两个字符串是否相等。

此方法会将两个值先转换为字符串再进行比较，例如 string_equals(1,"1") 不会报错


`length_equals`: checked_value 的长度是否等于 expected_value

`length_greater_than`:checked_value 的长度是否大于 expected_value

`length_greater_than_or_equals`: checked_value 的长度是否大于等于 expected_value

`length_less_than`:checked_value 的长度是否小于 expected_value

`length_less_than_or_equals`:checked_value 的长度是否小于等于 expected_value


### Save
save 区块简单的说明就是会将一些值在运行完测试后保存进当前 stage 的可用变量中。

定制化的版本统一了 save 的写法，统一使用变量替换的方式来作为值的获取以及保存的唯一方式

```yml
---
stages:
- name: save stage
  request:
    url: 111
  response:
    save:
    # 在 save stage 中存下了 url 这个 key，当前 stage 可以使用这个 key 来做变量的替换
      url: "{request.url}"
- name: use stage
  request:
    url: "{url}"
  ...
```
被引用进来的 stage 在运行时是加入到真正在运行的 stage 的可用变量中的。


### Command Line Parameters

定制版本增加了以下参数:
* `tavern-function-cfg`: 声明一个函数来生成一个 variables 并且将其合并进 global variables 中.
* `tavern_base_dir`: 声明 include 查找文件的基准地址
```yml
---
name: test
includes:
  # 如果 地址是以 / 开头，首先会从系统的绝对地址查找是否有该文件，如果有，则直接使用，否则会在 base_dir 里查找 这个路径
  - !include /project/varaibles.yaml
  # 其他地址均以当前文件的地址作为相对查找地址
  - !include ./project/variables.yaml

```


### 其他细节改动
* 扫描文件的格式的改动。 `test_xxx.tavern.yaml` -> `stage_xxx.yaml`
* reference stage 的改动
```yml
---
name: ref stage
stages:
  - id: ref_stage
    name: "abc"

---
name: main stage
stages:
  # tavern 旧的写法
  # - type: ref
  #   id : ref_stage
  # 精简了写法，直接使用 ref 关键字
  - ref: ref_stage

```