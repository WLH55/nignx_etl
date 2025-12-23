1. # 每天的请求量是多少

   大概几万或者十几万的一个量级。 

   

   如果按照每秒的并发？ qps是在是多少左右？

   

   

   

   

   

   

   # 数据量多少 选择哪种存储方式

   数据量可能在TB 级别。

   

   那么 以下的数据库选择哪个比较合适

   1. mysql?  高并发性能不好。日志信息写入频繁，mysql需要动态维护B+索引结构，插入性能差。
   2. es ? 全文搜索 错误日志检索 运维难度高 内存占用高，检索速度快 适合做系统运行日志监控平台，不适合做埋点日志分析平台 ❌	
   3.   clickhouse?  高压缩率  节省空间。支持TB 级的存储   OLAP（联机分析处理）数据库 适合埋点数据的聚合查询，比如算平均值，求和，去重等。支持sql。 

   

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

   

   

   

   # 埋点日志格式

   根据需求 设计请求数据的格式。

   大概有以下这么几种设计风格

   

   

   https://blog.csdn.net/goTsHgo/article/details/143307009

   

   

   

   

   

   

   

   # 是离线处理日志还是实时处理日志

   意思是 运营方需要实时查看埋点数据分析  还是 分批收集埋点数据之后在某一个时间点统一分析。

   

   

   

   

   # 日志收集组件

   在我们的需求当中需要采集nginx 的请求日志，所以就需要有对应的日志采集组件。以下是主流的采集组件。

   

   

   1. flume
   2. logstash
   3. filebeat

   这篇文章是关于他们之间对比的介绍

   https://cloud.tencent.com/developer/article/1651643

   

   总结来说 从占用资源角度来说 flume > logstash > filebeat

   logstash 和 filebeat是同一个生态里面的组件。  logstash 侧重于 数据过滤 filebeat 侧重于数据采集。

   所以一般 将 filebeat和 logstash 搭配使用。

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

   

   下面这篇文章是关于 filebeat 和 logstash 搭配使用的案例

   https://help.aliyun.com/zh/es/use-cases/use-filebeat-kafka-logstash-and-elasticsearch-to-build-a-log-analysis-system

   

   

   ![img](https://cdn.nlark.com/yuque/0/2025/png/28467887/1766394135177-8d64d2a8-c54b-4b36-94e8-d23d8b58169b.png)

   

   

   

   这篇文章是 介绍 三种采集nginx 日志的方式

   https://cloud.tencent.com/developer/article/1895982

   

   

   

   # 可视化分析界面

   如果需要可视化的分析界面 以下有开源免费的选择

    QuickBI / Metabase  

   

   

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

   

   # 方案二 云服务器方案  ❌ 采用自研方案

   

   之前的埋点使用bigquery 进行存储吗？

   - **数据收集**：使用云服务商提供的埋点SDK（如AWS Amplify、Google Analytics的SDK）。
   - **数据传输**：SDK直接发送到云服务商的网关。
   - **数据存储**：存储在云存储（如AWS S3、Google Cloud Storage）和云数据仓库（如AWS Redshift、Google BigQuery）中。
   - **数据分析**：使用云上的BI工具（如AWS QuickSight、Google Data Studio）或直接使用SQL查询数据仓库。

   #### 

   # 方案三  使用第三方分析平台 ❌采用自研方案

   - **数据收集**：使用第三方分析平台（如Mixpanel、神策数据、GrowingIO）提供的SDK。
   - **数据传输**：SDK直接发送到第三方平台。
   - **数据存储和分析**：由第三方平台负责，用户通过其提供的界面进行数据分析。