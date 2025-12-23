1. 请求的qps 大概是多少，在什么样的量级。

一秒打到nginx的请求大概有多少。



一天 传输的数据量多大？ 







1. 使用哪种存储方式。

  mysql?  高并发性能不好。日志信息写入频繁，mysql需要动态维护B+索引结构，插入性能差。

  es ? 全文搜索 错误日志检索 运维难度高 内存占用高

  clickhouse?  高压缩率  节省空间



```python
# 测试数据：1亿条Nginx日志（原始大小500GB）
ClickHouse:
  - 压缩后: 50GB (10:1压缩比)
  - 查询内存: 2-4GB

Elasticsearch:
  - 压缩后: 250GB (2:1压缩比)
  - JVM堆内存: 32GB+
  - 磁盘I/O: 高
```





3.埋点日志格式

https://blog.csdn.net/goTsHgo/article/details/143307009



https://zhuanlan.zhihu.com/p/644137017













4 是离线处理日志还是实时处理日志





5日志收集组件

flume  logstash 	filebeat

https://cloud.tencent.com/developer/article/1651643



https://help.aliyun.com/zh/es/use-cases/use-filebeat-kafka-logstash-and-elasticsearch-to-build-a-log-analysis-system



![img](https://cdn.nlark.com/yuque/0/2025/png/28467887/1766394135177-8d64d2a8-c54b-4b36-94e8-d23d8b58169b.png)



推荐 fliebeat + logstash 方案  

```python
为什么这么选？
Filebeat擅长收集：文件监控、断点续传、负载均衡

Logstash擅长处理：强大的grok、丰富的插件、易调试

分工明确：各司其职，架构清晰

易于扩展：未来需要更复杂处理时，直接在Logstash中添加

配置要点
Filebeat：只做收集，关闭复杂处理

Logstash：承担所有解析和转换逻辑

ClickHouse：接收结构化数据，专注于存储和查询
```





6如何采集nginx日志

https://cloud.tencent.com/developer/article/1895982





# 方案一 nginx + filebeat + logrotate +clickhouse



通过http请求发送到nginx , nginx 将请求的json数据写入日志到本地文件。logrotate用于分割日志文件，防止单个日志文件太大

然后使用fliebeat实时读取日志，存储到clickhouse 当中。  看请求的量级  如果请求量级很大 可以引入kafka 作为流量的削峰填谷。



```python
# 直接写入，不要Kafka
Nginx → 日志文件 → Filebeat → Elasticsearch/ClickHouse

适用条件：
- 数据量 < 10GB/天
- 允许偶尔数据丢失
- 查询需求简单
- 团队规模小
```





```python
Nginx → 日志文件 → Filebeat → Kafka → ClickHouse

触发条件：
1. 数据量 > 50GB/天
2. 需要7x24小时服务
3. 有多个数据使用方
4. 有突发流量场景
```



# 方案二 云服务器方案 



之前的埋点使用bigquery 进行存储吗？

- **数据收集**：使用云服务商提供的埋点SDK（如AWS Amplify、Google Analytics的SDK）。
- **数据传输**：SDK直接发送到云服务商的网关。
- **数据存储**：存储在云存储（如AWS S3、Google Cloud Storage）和云数据仓库（如AWS Redshift、Google BigQuery）中。
- **数据分析**：使用云上的BI工具（如AWS QuickSight、Google Data Studio）或直接使用SQL查询数据仓库。

#### 

# 方案三  使用第三方分析平台 ❌

- **数据收集**：使用第三方分析平台（如Mixpanel、神策数据、GrowingIO）提供的SDK。
- **数据传输**：SDK直接发送到第三方平台。
- **数据存储和分析**：由第三方平台负责，用户通过其提供的界面进行数据分析。