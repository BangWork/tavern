## ONES Tavern 定制化修改

###Validation

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
上面的 return 指代表真正对应的 comparators 方法，上面的数组则是 comparators 的别名，意思是，可以使用别名来做为 validator 的 key

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