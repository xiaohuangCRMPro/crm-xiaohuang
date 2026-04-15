const express = require('express');
const { Pool } = require('pg');
const multer = require('multer');
const XLSX = require('xlsx');
const cors = require('cors');

const app = express();
app.use(express.json());
app.use(cors());

const pool = new Pool({
  user: 'postgres',
  password: '123456',
  host: 'localhost',
  port: 5432,
  database: 'crm'
});

const upload = multer({ dest: 'uploads/' });

/* =========================
   上传数据
========================= */
app.post('/upload', upload.single('file'), async (req, res) => {
  const wb = XLSX.readFile(req.file.path);
  const sheet = wb.Sheets[wb.SheetNames[0]];
  const data = XLSX.utils.sheet_to_json(sheet);

  for (let row of data) {
    const { user_id, deposit, withdraw, login_count } = row;

    if (deposit > 0) {
      await pool.query(
        `INSERT INTO transactions(user_id,type,amount) VALUES($1,'deposit',$2)`,
        [user_id, deposit]
      );
    }

    if (withdraw > 0) {
      await pool.query(
        `INSERT INTO transactions(user_id,type,amount) VALUES($1,'withdraw',$2)`,
        [user_id, withdraw]
      );
    }

    for (let i = 0; i < login_count; i++) {
      await pool.query(
        `INSERT INTO login_logs(user_id) VALUES($1)`,
        [user_id]
      );
    }
  }

  res.json({ message: '上传成功' });
});

/* =========================
   用户列表
========================= */
app.get('/users', async (req, res) => {
  const result = await pool.query(`
    SELECT *,
    DATE_PART('day', NOW() - last_login_time) AS 不登录天数
    FROM users
  `);

  res.json({
    message: '用户列表',
    data: result.rows
  });
});

/* =========================
   重新计算
========================= */
app.post('/recalculate', async (req, res) => {
  await pool.query(`
    UPDATE users u SET
    total_deposit = (
      SELECT COALESCE(SUM(amount),0)
      FROM transactions WHERE user_id=u.user_id AND type='deposit'
    ),
    total_withdraw = (
      SELECT COALESCE(SUM(amount),0)
      FROM transactions WHERE user_id=u.user_id AND type='withdraw'
    ),
    last_login_time = (
      SELECT MAX(login_time)
      FROM login_logs WHERE user_id=u.user_id
    )
  `);

  res.json({ message: '计算完成' });
});

/* =========================
   分类
========================= */
app.get('/classify', async (req, res) => {
  const result = await pool.query(`
    SELECT *,
    DATE_PART('day', NOW() - last_login_time) AS days
    FROM users
  `);

  const data = result.rows.map(u => {
    let level = '流失用户';

    if (u.total_deposit > 50000 && u.days <= 3) level = 'VIP用户';
    else if (u.days <= 3) level = '活跃用户';
    else if (u.days <= 7) level = '警告用户';
    if (u.total_withdraw > u.total_deposit) level = '风险用户';

    return {
      用户ID: u.user_id,
      总充值: u.total_deposit,
      总提现: u.total_withdraw,
      不登录天数: u.days,
      用户等级: level
    };
  });

  res.json({
    message: '分类结果',
    data
  });
});

/* =========================
   奖金建议
========================= */
app.get('/bonus', async (req, res) => {
  const result = await pool.query(`
    SELECT u.user_id,
           u.total_deposit,
           DATE_PART('day', NOW() - u.last_login_time) AS days,
           r.percent
    FROM users u
    JOIN bonus_rules r
    ON DATE_PART('day', NOW() - u.last_login_time)
    BETWEEN r.min_days AND r.max_days
  `);

  const data = result.rows.map(u => ({
    用户ID: u.user_id,
    建议奖金: (u.total_deposit * u.percent / 100).toFixed(2)
  }));

  res.json({
    message: '奖金建议',
    data
  });
});

/* =========================
   启动
========================= */
app.listen(3000, () => {
  console.log('后台运行 http://localhost:3000');
});
