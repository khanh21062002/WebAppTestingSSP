# -*- coding: utf-8 -*-
"""
Seed 100 câu trắc nghiệm Python vào ngân hàng câu hỏi.
Chạy:  python manage.py seed_python_questions
       python manage.py seed_python_questions --reset   (xóa câu cũ của môn này trước khi thêm)
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from questions.models import Subject, Topic, Question, Choice

User = get_user_model()

SUBJECT_NAME = 'Lập trình Python'
SUBJECT_CODE = 'PY101'

# Mỗi câu: (loại, độ khó, nội dung, [(nhãn, nội dung, đúng?)...], giải thích)
# loại: single / multiple / true_false
S, M, TF = 'single', 'multiple', 'true_false'
E, ME, H = 'easy', 'medium', 'hard'


def tf(answer_true):
    """Sinh 2 đáp án Đúng/Sai cho câu true_false."""
    return [('Đ', 'Đúng', answer_true), ('S', 'Sai', not answer_true)]


QUESTIONS = [
    # ───────── Cơ bản & kiểu dữ liệu (easy) ─────────
    (S, E, 'Hàm nào dùng để in dữ liệu ra màn hình trong Python?',
     [('A', 'echo()', False), ('B', 'print()', True), ('C', 'printf()', False), ('D', 'console.log()', False)],
     'print() là hàm chuẩn để xuất dữ liệu ra màn hình.'),

    (S, E, 'Kiểu dữ liệu nào dùng để lưu số nguyên trong Python?',
     [('A', 'str', False), ('B', 'int', True), ('C', 'float', False), ('D', 'bool', False)],
     'int là kiểu số nguyên.'),

    (S, E, 'Kiểu dữ liệu nào dùng để lưu số thực (số thập phân)?',
     [('A', 'int', False), ('B', 'double', False), ('C', 'float', True), ('D', 'decimal', False)],
     'float lưu số thực; double không phải kiểu built-in của Python.'),

    (S, E, 'Hàm len("Python") trả về giá trị nào?',
     [('A', '5', False), ('B', '6', True), ('C', '7', False), ('D', 'Lỗi', False)],
     'Chuỗi "Python" có 6 ký tự.'),

    (S, E, 'Hàm input() trong Python luôn trả về dữ liệu kiểu gì?',
     [('A', 'int', False), ('B', 'str', True), ('C', 'float', False), ('D', 'tùy người dùng nhập', False)],
     'input() luôn trả về chuỗi (str).'),

    (S, E, 'Ký hiệu nào dùng để viết chú thích (comment) một dòng?',
     [('A', '//', False), ('B', '#', True), ('C', '/* */', False), ('D', '--', False)],
     'Python dùng # cho comment một dòng.'),

    (S, E, 'Toán tử nào dùng để tính lũy thừa trong Python?',
     [('A', '^', False), ('B', '**', True), ('C', 'pow', False), ('D', '//', False)],
     '2 ** 3 = 8. Toán tử ** là lũy thừa.'),

    (S, E, 'Kết quả của 7 // 2 là bao nhiêu?',
     [('A', '3.5', False), ('B', '3', True), ('C', '4', False), ('D', '1', False)],
     '// là phép chia lấy phần nguyên: 7 // 2 = 3.'),

    (S, E, 'Kết quả của 8 % 3 là bao nhiêu?',
     [('A', '2', True), ('B', '1', False), ('C', '0', False), ('D', '2.67', False)],
     '% là phép chia lấy dư: 8 chia 3 được 2 dư 2, nên 8 % 3 = 2.'),

    (S, E, 'Giá trị nào sau đây là kiểu boolean hợp lệ trong Python?',
     [('A', 'true', False), ('B', 'TRUE', False), ('C', 'True', True), ('D', '"True"', False)],
     'Python viết hoa chữ cái đầu: True / False.'),

    (S, E, 'int("10") cho kết quả gì?',
     [('A', 'Chuỗi "10"', False), ('B', 'Số nguyên 10', True), ('C', 'Lỗi', False), ('D', '10.0', False)],
     'int() chuyển chuỗi "10" thành số nguyên 10.'),

    (S, E, 'Kết quả của "abc" + "def" là gì?',
     [('A', 'abcdef', True), ('B', 'abc def', False), ('C', 'Lỗi', False), ('D', 'abc+def', False)],
     'Toán tử + nối hai chuỗi: "abcdef".'),

    (S, E, 'Kết quả của "ab" * 3 là gì?',
     [('A', 'ababab', True), ('B', 'ab3', False), ('C', 'Lỗi', False), ('D', 'ab ab ab', False)],
     'Chuỗi nhân số nguyên sẽ lặp lại: "ababab".'),

    (S, E, 'Hàm nào trả về kiểu dữ liệu của một biến?',
     [('A', 'typeof()', False), ('B', 'type()', True), ('C', 'kind()', False), ('D', 'datatype()', False)],
     'type(x) trả về kiểu của x.'),

    (S, E, 'Cách khai báo biến đúng trong Python?',
     [('A', 'int x = 5', False), ('B', 'x = 5', True), ('C', 'var x = 5', False), ('D', 'let x = 5', False)],
     'Python không khai báo kiểu: x = 5.'),

    # ───────── Chuỗi (string) ─────────
    (S, E, 'Phương thức nào chuyển chuỗi thành chữ HOA?',
     [('A', '.lower()', False), ('B', '.upper()', True), ('C', '.capitalize()', False), ('D', '.title()', False)],
     '.upper() trả về chuỗi viết hoa toàn bộ.'),

    (S, ME, 'Kết quả của "Python"[1:4] là gì?',
     [('A', 'Pyt', False), ('B', 'yth', True), ('C', 'ytho', False), ('D', 'Pyth', False)],
     'Slicing [1:4] lấy ký tự chỉ số 1,2,3: "yth".'),

    (S, ME, 'Kết quả của "Python"[-1] là gì?',
     [('A', 'P', False), ('B', 'n', True), ('C', 'o', False), ('D', 'Lỗi', False)],
     'Chỉ số -1 là ký tự cuối: "n".'),

    (S, ME, 'Phương thức nào tách chuỗi thành danh sách theo dấu phân cách?',
     [('A', '.join()', False), ('B', '.split()', True), ('C', '.replace()', False), ('D', '.find()', False)],
     '.split(",") tách chuỗi thành list.'),

    (S, ME, '"a,b,c".split(",") cho kết quả gì?',
     [('A', "['a', 'b', 'c']", True), ('B', "'abc'", False), ('C', "['a,b,c']", False), ('D', 'Lỗi', False)],
     "split tách theo dấu phẩy thành ['a', 'b', 'c']."),

    (S, ME, "Kết quả của \"-\".join(['a','b','c']) là gì?",
     [('A', 'abc', False), ('B', 'a-b-c', True), ('C', "['a-b-c']", False), ('D', 'Lỗi', False)],
     'join nối các phần tử bằng "-": "a-b-c".'),

    (S, ME, 'Phương thức .strip() làm gì với chuỗi?',
     [('A', 'Xóa khoảng trắng đầu và cuối', True), ('B', 'Chuyển thành chữ thường', False),
      ('C', 'Đảo ngược chuỗi', False), ('D', 'Xóa toàn bộ khoảng trắng', False)],
     '.strip() loại bỏ khoảng trắng (và xuống dòng) ở hai đầu chuỗi.'),

    (S, ME, 'Cách nào tạo f-string đúng trong Python?',
     [('A', 'f"Xin chào {ten}"', True), ('B', '"Xin chào {ten}"', False),
      ('C', 's"Xin chào {ten}"', False), ('D', '"Xin chào %ten"', False)],
     'f-string bắt đầu bằng f và dùng {} để chèn biến.'),

    (S, ME, 'Phương thức nào kiểm tra chuỗi có bắt đầu bằng tiền tố cho trước?',
     [('A', '.endswith()', False), ('B', '.startswith()', True), ('C', '.contains()', False), ('D', '.index()', False)],
     '.startswith("abc") trả về True nếu chuỗi bắt đầu bằng "abc".'),

    # ───────── List ─────────
    (S, E, 'Cách khai báo một danh sách (list) rỗng?',
     [('A', '{}', False), ('B', '[]', True), ('C', '()', False), ('D', 'list{}', False)],
     '[] tạo list rỗng; {} tạo dict rỗng.'),

    (S, E, 'Phương thức nào thêm một phần tử vào cuối list?',
     [('A', '.add()', False), ('B', '.append()', True), ('C', '.insert()', False), ('D', '.push()', False)],
     '.append(x) thêm x vào cuối list.'),

    (S, ME, 'Phương thức nào thêm phần tử vào vị trí chỉ định trong list?',
     [('A', '.append()', False), ('B', '.insert()', True), ('C', '.add()', False), ('D', '.put()', False)],
     '.insert(i, x) chèn x vào vị trí i.'),

    (S, ME, 'Kết quả của [1, 2, 3][::-1] là gì?',
     [('A', '[1, 2, 3]', False), ('B', '[3, 2, 1]', True), ('C', '[1, 3]', False), ('D', 'Lỗi', False)],
     '[::-1] đảo ngược list: [3, 2, 1].'),

    (S, ME, 'Phương thức nào xóa và trả về phần tử cuối của list?',
     [('A', '.remove()', False), ('B', '.pop()', True), ('C', '.delete()', False), ('D', '.discard()', False)],
     '.pop() xóa và trả về phần tử cuối (mặc định).'),

    (S, ME, 'Hàm nào trả về số phần tử lớn nhất trong list số?',
     [('A', 'max()', True), ('B', 'top()', False), ('C', 'highest()', False), ('D', 'big()', False)],
     'max([1,5,3]) trả về 5.'),

    (S, ME, 'len([1, [2, 3], 4]) cho kết quả gì?',
     [('A', '2', False), ('B', '3', True), ('C', '4', False), ('D', '5', False)],
     'List có 3 phần tử: 1, [2,3], 4 → len = 3.'),

    (S, ME, 'Cách nào sắp xếp list tăng dần tại chỗ (in-place)?',
     [('A', 'list.sort()', True), ('B', 'sort(list)', False), ('C', 'list.sorted()', False), ('D', 'list.order()', False)],
     '.sort() sắp xếp ngay trên list; sorted() trả về list mới.'),

    (S, H, 'a = [1,2,3]; b = a; b.append(4). Giá trị của a bây giờ là gì?',
     [('A', '[1, 2, 3]', False), ('B', '[1, 2, 3, 4]', True), ('C', '[4]', False), ('D', 'Lỗi', False)],
     'b = a tham chiếu cùng list, nên a cũng thay đổi thành [1,2,3,4].'),

    # ───────── Tuple / Set / Dict ─────────
    (S, ME, 'Đặc điểm nào sau đây ĐÚNG về tuple?',
     [('A', 'Có thể thay đổi phần tử', False), ('B', 'Không thể thay đổi (immutable)', True),
      ('C', 'Không cho phép trùng lặp', False), ('D', 'Dùng dấu {}', False)],
     'Tuple là bất biến (immutable).'),

    (S, E, 'Cách khai báo dictionary đúng?',
     [('A', "{'a': 1, 'b': 2}", True), ('B', "['a': 1]", False), ('C', "('a', 1)", False), ('D', "<a: 1>", False)],
     "Dict dùng {khóa: giá trị}."),

    (S, ME, "Với d = {'x': 10}, cách lấy giá trị theo khóa 'x'?",
     [('A', "d.x", False), ('B', "d['x']", True), ('C', "d(x)", False), ('D', "d->x", False)],
     "Truy cập dict bằng d['x'] → 10."),

    (S, ME, 'Cấu trúc dữ liệu nào KHÔNG cho phép phần tử trùng lặp?',
     [('A', 'list', False), ('B', 'tuple', False), ('C', 'set', True), ('D', 'str', False)],
     'set chỉ chứa các phần tử duy nhất.'),

    (S, ME, "Phương thức nào lấy giá trị an toàn từ dict, trả về None nếu không có khóa?",
     [('A', '.get()', True), ('B', '.value()', False), ('C', '.find()', False), ('D', '.fetch()', False)],
     "d.get('k') trả về None nếu khóa không tồn tại thay vì báo lỗi."),

    (S, ME, "Phương thức nào trả về tất cả các khóa của dict?",
     [('A', '.values()', False), ('B', '.keys()', True), ('C', '.items()', False), ('D', '.all()', False)],
     "d.keys() trả về danh sách các khóa."),

    (S, H, 'len({1, 2, 2, 3, 3, 3}) cho kết quả gì?',
     [('A', '6', False), ('B', '3', True), ('C', '2', False), ('D', 'Lỗi', False)],
     'set loại trùng lặp còn {1,2,3} → len = 3.'),

    # ───────── Toán tử & điều kiện ─────────
    (S, E, 'Toán tử nào dùng để so sánh BẰNG NHAU?',
     [('A', '=', False), ('B', '==', True), ('C', '===', False), ('D', '!=', False)],
     '== so sánh bằng; = là phép gán.'),

    (S, E, 'Toán tử logic "và" trong Python là gì?',
     [('A', '&&', False), ('B', 'and', True), ('C', 'AND', False), ('D', '&', False)],
     'Python dùng từ khóa and.'),

    (S, ME, 'Kết quả của: True and False là gì?',
     [('A', 'True', False), ('B', 'False', True), ('C', 'None', False), ('D', 'Lỗi', False)],
     'and chỉ True khi cả hai True; ở đây False.'),

    (S, ME, 'Kết quả của: not (5 > 3) là gì?',
     [('A', 'True', False), ('B', 'False', True), ('C', '5', False), ('D', 'Lỗi', False)],
     '5 > 3 là True, not True = False.'),

    (S, ME, 'Câu lệnh nào dùng để rẽ nhánh điều kiện trong Python?',
     [('A', 'switch', False), ('B', 'if / elif / else', True), ('C', 'when', False), ('D', 'case', False)],
     'Python dùng if / elif / else.'),

    (S, H, 'Kết quả của: 5 if 3 > 2 else 10',
     [('A', '5', True), ('B', '10', False), ('C', 'True', False), ('D', 'Lỗi', False)],
     'Toán tử ba ngôi: vì 3 > 2 đúng nên trả về 5.'),

    (S, H, 'Kết quả của biểu thức: bool("") ',
     [('A', 'True', False), ('B', 'False', True), ('C', 'None', False), ('D', 'Lỗi', False)],
     'Chuỗi rỗng "" được coi là False (falsy).'),

    (S, H, 'Kết quả của: 0 or "Python"',
     [('A', '0', False), ('B', 'Python', True), ('C', 'True', False), ('D', 'False', False)],
     'or trả về toán hạng đầu tiên truthy; 0 là falsy nên trả "Python".'),

    # ───────── Vòng lặp ─────────
    (S, E, 'Vòng lặp nào dùng để lặp qua các phần tử của một list?',
     [('A', 'for', True), ('B', 'loop', False), ('C', 'foreach', False), ('D', 'repeat', False)],
     'for item in list: ... duyệt qua từng phần tử.'),

    (S, ME, 'range(5) tạo ra dãy số nào?',
     [('A', '1,2,3,4,5', False), ('B', '0,1,2,3,4', True), ('C', '0,1,2,3,4,5', False), ('D', '5', False)],
     'range(5) cho 0 đến 4.'),

    (S, ME, 'range(2, 8, 2) tạo ra các số nào?',
     [('A', '2,4,6', True), ('B', '2,4,6,8', False), ('C', '2,3,4,5,6,7', False), ('D', '2,8', False)],
     'range(start, stop, step): 2,4,6 (dừng trước 8).'),

    (S, ME, 'Từ khóa nào dùng để thoát khỏi vòng lặp ngay lập tức?',
     [('A', 'continue', False), ('B', 'break', True), ('C', 'stop', False), ('D', 'exit', False)],
     'break thoát khỏi vòng lặp.'),

    (S, ME, 'Từ khóa nào bỏ qua phần còn lại của vòng lặp hiện tại và sang lần lặp tiếp theo?',
     [('A', 'break', False), ('B', 'continue', True), ('C', 'pass', False), ('D', 'skip', False)],
     'continue chuyển sang lần lặp kế tiếp.'),

    (S, H, 'Vòng for...else trong Python: khối else chạy khi nào?',
     [('A', 'Khi vòng lặp bị break', False), ('B', 'Khi vòng lặp kết thúc bình thường (không break)', True),
      ('C', 'Luôn luôn chạy', False), ('D', 'Không bao giờ chạy', False)],
     'else của for chỉ chạy khi vòng lặp KHÔNG bị break.'),

    # ───────── Hàm ─────────
    (S, E, 'Từ khóa nào dùng để định nghĩa một hàm?',
     [('A', 'function', False), ('B', 'def', True), ('C', 'func', False), ('D', 'define', False)],
     'def tên_hàm(): để định nghĩa hàm.'),

    (S, ME, 'Từ khóa nào dùng để trả về giá trị từ hàm?',
     [('A', 'return', True), ('B', 'yield', False), ('C', 'give', False), ('D', 'output', False)],
     'return trả giá trị về nơi gọi hàm.'),

    (S, ME, 'Một hàm không có lệnh return sẽ trả về gì?',
     [('A', '0', False), ('B', 'None', True), ('C', 'False', False), ('D', 'Lỗi', False)],
     'Hàm không return mặc định trả về None.'),

    (S, H, 'def f(a, b=2): return a+b. Gọi f(3) trả về gì?',
     [('A', '3', False), ('B', '5', True), ('C', '2', False), ('D', 'Lỗi', False)],
     'b mặc định = 2 nên f(3) = 3 + 2 = 5.'),

    (S, H, '*args trong định nghĩa hàm cho phép điều gì?',
     [('A', 'Nhận số lượng tham số vị trí tùy ý', True), ('B', 'Nhận tham số kiểu từ khóa', False),
      ('C', 'Bắt buộc đúng 1 tham số', False), ('D', 'Không nhận tham số', False)],
     '*args gom các tham số vị trí thành một tuple.'),

    (S, H, '**kwargs trong hàm gom các tham số dạng gì?',
     [('A', 'List', False), ('B', 'Tuple', False), ('C', 'Dictionary (khóa-giá trị)', True), ('D', 'Set', False)],
     '**kwargs gom tham số dạng từ khóa thành dict.'),

    (S, H, 'Hàm lambda trong Python dùng để làm gì?',
     [('A', 'Tạo hàm ẩn danh ngắn gọn', True), ('B', 'Tạo lớp', False),
      ('C', 'Khai báo biến toàn cục', False), ('D', 'Xử lý ngoại lệ', False)],
     'lambda tạo hàm ẩn danh: lambda x: x*2.'),

    # ───────── List comprehension ─────────
    (S, H, 'Kết quả của [x*2 for x in range(3)] là gì?',
     [('A', '[0, 2, 4]', True), ('B', '[2, 4, 6]', False), ('C', '[0, 1, 2]', False), ('D', '[1, 2, 3]', False)],
     'range(3)=0,1,2 nhân 2 → [0, 2, 4].'),

    (S, H, 'Kết quả của [x for x in range(10) if x % 2 == 0] là gì?',
     [('A', '[1,3,5,7,9]', False), ('B', '[0,2,4,6,8]', True), ('C', '[0..9]', False), ('D', '[2,4,6,8,10]', False)],
     'Lọc các số chẵn từ 0-9: [0,2,4,6,8].'),

    (S, H, 'Cú pháp {x: x**2 for x in range(3)} tạo ra cấu trúc gì?',
     [('A', 'set', False), ('B', 'list', False), ('C', 'dict comprehension', True), ('D', 'tuple', False)],
     'Đây là dict comprehension → {0:0, 1:1, 2:4}.'),

    # ───────── OOP ─────────
    (S, ME, 'Từ khóa nào dùng để định nghĩa một lớp (class)?',
     [('A', 'class', True), ('B', 'object', False), ('C', 'struct', False), ('D', 'def', False)],
     'class TenLop: định nghĩa lớp.'),

    (S, H, 'Phương thức đặc biệt nào được gọi khi khởi tạo một đối tượng?',
     [('A', '__start__', False), ('B', '__init__', True), ('C', '__new__', False), ('D', '__create__', False)],
     '__init__ là hàm khởi tạo (constructor).'),

    (S, H, 'Tham số đầu tiên của phương thức instance trong class thường là gì?',
     [('A', 'this', False), ('B', 'self', True), ('C', 'cls', False), ('D', 'me', False)],
     'self tham chiếu đến chính đối tượng.'),

    (S, H, 'Tính chất nào của OOP cho phép lớp con kế thừa từ lớp cha?',
     [('A', 'Đóng gói (Encapsulation)', False), ('B', 'Kế thừa (Inheritance)', True),
      ('C', 'Đa hình (Polymorphism)', False), ('D', 'Trừu tượng (Abstraction)', False)],
     'Kế thừa cho phép tái sử dụng thuộc tính/phương thức của lớp cha.'),

    (S, H, 'Phương thức __str__ trong class dùng để làm gì?',
     [('A', 'Khởi tạo đối tượng', False), ('B', 'Định nghĩa chuỗi biểu diễn đối tượng khi print()', True),
      ('C', 'So sánh hai đối tượng', False), ('D', 'Xóa đối tượng', False)],
     '__str__ trả về chuỗi hiển thị khi dùng print(obj) hoặc str(obj).'),

    # ───────── Ngoại lệ (Exception) ─────────
    (S, ME, 'Khối nào dùng để bắt và xử lý ngoại lệ?',
     [('A', 'try / except', True), ('B', 'catch / throw', False), ('C', 'do / catch', False), ('D', 'check / error', False)],
     'Python dùng try / except.'),

    (S, H, 'Khối finally trong try/except chạy khi nào?',
     [('A', 'Chỉ khi có lỗi', False), ('B', 'Chỉ khi không có lỗi', False),
      ('C', 'Luôn luôn chạy dù có lỗi hay không', True), ('D', 'Không bao giờ chạy', False)],
     'finally luôn được thực thi để dọn dẹp tài nguyên.'),

    (S, H, 'Lỗi nào xảy ra khi chia một số cho 0?',
     [('A', 'ValueError', False), ('B', 'ZeroDivisionError', True), ('C', 'TypeError', False), ('D', 'IndexError', False)],
     '10 / 0 gây ZeroDivisionError.'),

    (S, H, 'Truy cập list[10] khi list chỉ có 3 phần tử gây ra lỗi gì?',
     [('A', 'KeyError', False), ('B', 'IndexError', True), ('C', 'ValueError', False), ('D', 'TypeError', False)],
     'Truy cập chỉ số ngoài phạm vi → IndexError.'),

    (S, H, 'Truy cập một khóa không tồn tại bằng d[key] gây lỗi gì?',
     [('A', 'IndexError', False), ('B', 'KeyError', True), ('C', 'NameError', False), ('D', 'AttributeError', False)],
     'Khóa không tồn tại trong dict → KeyError.'),

    (S, H, 'int("abc") gây ra lỗi gì?',
     [('A', 'ValueError', True), ('B', 'TypeError', False), ('C', 'SyntaxError', False), ('D', 'KeyError', False)],
     'Không chuyển được "abc" thành số → ValueError.'),

    # ───────── Module / file ─────────
    (S, ME, 'Từ khóa nào dùng để nhập một module?',
     [('A', 'include', False), ('B', 'import', True), ('C', 'using', False), ('D', 'require', False)],
     'import math để dùng module math.'),

    (S, H, 'Để dùng hàm sqrt từ module math, cách viết nào đúng?',
     [('A', 'from math import sqrt', True), ('B', 'import sqrt from math', False),
      ('C', 'include math.sqrt', False), ('D', 'use math.sqrt', False)],
     'from math import sqrt rồi gọi sqrt(x).'),

    (S, H, 'Chế độ "w" khi mở file bằng open() có ý nghĩa gì?',
     [('A', 'Đọc file', False), ('B', 'Ghi đè (tạo mới/xóa nội dung cũ)', True),
      ('C', 'Ghi thêm vào cuối', False), ('D', 'Đọc và ghi', False)],
     '"w" mở để ghi, xóa nội dung cũ nếu file đã tồn tại.'),

    (S, H, 'Câu lệnh nào đảm bảo file tự động được đóng sau khi dùng?',
     [('A', 'with open(...) as f:', True), ('B', 'open(...).close()', False),
      ('C', 'try open(...)', False), ('D', 'file open(...)', False)],
     'with quản lý ngữ cảnh, tự đóng file khi rời khối lệnh.'),

    # ───────── Nâng cao ─────────
    (S, H, 'Từ khóa nào tạo ra một generator thay vì return?',
     [('A', 'return', False), ('B', 'yield', True), ('C', 'gen', False), ('D', 'async', False)],
     'yield tạo generator, trả giá trị lần lượt và giữ trạng thái.'),

    (S, H, 'Hàm enumerate() khi duyệt list trả về gì?',
     [('A', 'Chỉ giá trị', False), ('B', 'Cặp (chỉ số, giá trị)', True),
      ('C', 'Chỉ chỉ số', False), ('D', 'Độ dài list', False)],
     'enumerate trả về (index, value) cho mỗi phần tử.'),

    (S, H, 'Hàm zip([1,2],[3,4]) tạo ra các cặp nào?',
     [('A', '(1,3) và (2,4)', True), ('B', '(1,2) và (3,4)', False),
      ('C', '(1,4) và (2,3)', False), ('D', 'Lỗi', False)],
     'zip ghép phần tử cùng vị trí: (1,3), (2,4).'),

    (S, H, 'Hàm map(func, iterable) dùng để làm gì?',
     [('A', 'Lọc phần tử theo điều kiện', False), ('B', 'Áp dụng hàm lên từng phần tử', True),
      ('C', 'Sắp xếp', False), ('D', 'Gộp về một giá trị', False)],
     'map áp dụng func cho mỗi phần tử của iterable.'),

    (S, H, 'Hàm filter(func, iterable) trả về gì?',
     [('A', 'Các phần tử mà func trả về True', True), ('B', 'Tất cả phần tử', False),
      ('C', 'Phần tử đầu tiên', False), ('D', 'Tổng các phần tử', False)],
     'filter giữ lại phần tử thỏa điều kiện func.'),

    (S, H, 'Decorator trong Python (cú pháp @) dùng để làm gì?',
     [('A', 'Trang trí giao diện', False), ('B', 'Bọc/mở rộng hành vi của hàm mà không sửa hàm gốc', True),
      ('C', 'Khai báo biến', False), ('D', 'Import module', False)],
     'Decorator bao một hàm để thêm hành vi (logging, kiểm tra quyền...).'),

    (S, H, 'Kết quả của list(range(0)) là gì?',
     [('A', '[0]', False), ('B', '[]', True), ('C', '[0, 1]', False), ('D', 'Lỗi', False)],
     'range(0) rỗng nên list() trả về [].'),

    (S, H, 'Sự khác biệt chính giữa is và == là gì?',
     [('A', 'Không có khác biệt', False),
      ('B', 'is so sánh danh tính (cùng object), == so sánh giá trị', True),
      ('C', '== so sánh danh tính, is so sánh giá trị', False),
      ('D', 'is chỉ dùng cho số', False)],
     'is kiểm tra hai biến cùng trỏ tới một đối tượng; == so sánh giá trị.'),

    (S, ME, 'Hàm nào trả về tổng các phần tử trong một list số?',
     [('A', 'total()', False), ('B', 'sum()', True), ('C', 'add()', False), ('D', 'count()', False)],
     'sum([1,2,3]) = 6.'),

    (S, ME, 'Hàm abs(-7) trả về giá trị nào?',
     [('A', '-7', False), ('B', '7', True), ('C', '0', False), ('D', 'Lỗi', False)],
     'abs trả về giá trị tuyệt đối: 7.'),

    (S, ME, 'Hàm round(3.14159, 2) trả về gì?',
     [('A', '3.14', True), ('B', '3.1', False), ('C', '3.142', False), ('D', '3', False)],
     'round làm tròn 2 chữ số thập phân: 3.14.'),

    (S, H, 'Kết quả của sorted([3, 1, 2], reverse=True) là gì?',
     [('A', '[1, 2, 3]', False), ('B', '[3, 2, 1]', True), ('C', '[3, 1, 2]', False), ('D', 'Lỗi', False)],
     'reverse=True sắp xếp giảm dần: [3, 2, 1].'),

    # ───────── Multiple choice (nhiều đáp án đúng) ─────────
    (M, ME, 'Những cấu trúc dữ liệu nào sau đây là KHẢ BIẾN (mutable)?',
     [('A', 'list', True), ('B', 'dict', True), ('C', 'tuple', False), ('D', 'set', True)],
     'list, dict, set là mutable; tuple là immutable.'),

    (M, ME, 'Những giá trị nào sau đây được coi là FALSY trong Python?',
     [('A', '0', True), ('B', '""', True), ('C', '[]', True), ('D', '"0"', False)],
     '0, chuỗi rỗng, list rỗng là falsy; "0" là chuỗi khác rỗng nên truthy.'),

    (M, H, 'Những phương thức nào sau đây thuộc về kiểu list?',
     [('A', 'append()', True), ('B', 'sort()', True), ('C', 'keys()', False), ('D', 'pop()', True)],
     'keys() là của dict; append, sort, pop là của list.'),

    (M, H, 'Những cách nào sau đây tạo ra một dictionary hợp lệ?',
     [('A', 'dict(a=1, b=2)', True), ('B', '{"a": 1}', True), ('C', '{}', True), ('D', '[1, 2]', False)],
     '[1,2] là list. Ba cách còn lại tạo dict.'),

    (M, ME, 'Những kiểu dữ liệu nào sau đây là kiểu số trong Python?',
     [('A', 'int', True), ('B', 'float', True), ('C', 'complex', True), ('D', 'str', False)],
     'int, float, complex là kiểu số; str là chuỗi.'),

    (M, H, 'Những phát biểu nào ĐÚNG về hàm trong Python?',
     [('A', 'Có thể có tham số mặc định', True), ('B', 'Có thể trả về nhiều giá trị (qua tuple)', True),
      ('C', 'Bắt buộc phải có return', False), ('D', 'Có thể được gán cho một biến', True)],
     'Hàm là đối tượng hạng nhất; return không bắt buộc.'),

    (M, H, 'Những toán tử nào sau đây là toán tử so sánh?',
     [('A', '==', True), ('B', '!=', True), ('C', '>=', True), ('D', '+=', False)],
     '+= là toán tử gán kết hợp, không phải so sánh.'),

    (M, ME, 'Những từ khóa nào dùng trong xử lý ngoại lệ?',
     [('A', 'try', True), ('B', 'except', True), ('C', 'finally', True), ('D', 'catch', False)],
     'Python dùng try/except/finally/raise; catch là của ngôn ngữ khác.'),

    # ───────── True/False ─────────
    (TF, E, 'Python là ngôn ngữ phân biệt chữ hoa và chữ thường (case-sensitive).',
     tf(True), 'Biến "Ten" và "ten" là khác nhau trong Python.'),

    (TF, E, 'Trong Python, danh sách (list) có thể chứa các phần tử thuộc nhiều kiểu dữ liệu khác nhau.',
     tf(True), 'Ví dụ [1, "a", 3.5, True] là hợp lệ.'),

    (TF, E, 'Tuple trong Python có thể thay đổi giá trị sau khi tạo.',
     tf(False), 'Tuple là immutable — không thể thay đổi sau khi tạo.'),

    (TF, ME, 'Chỉ số (index) của phần tử đầu tiên trong list là 0.',
     tf(True), 'Python đánh chỉ số bắt đầu từ 0.'),

    (TF, ME, 'Hàm print() tự động xuống dòng sau khi in, trừ khi đổi tham số end.',
     tf(True), 'Mặc định print có end="\\n". Có thể đổi: print(x, end="").'),

    (TF, ME, 'Trong Python, khối lệnh được xác định bằng dấu ngoặc nhọn {}.',
     tf(False), 'Python dùng thụt lề (indentation), không dùng {}.'),

    (TF, H, 'Biểu thức 0.1 + 0.2 == 0.3 trả về True trong Python.',
     tf(False), 'Do sai số dấu phẩy động, 0.1 + 0.2 = 0.30000000000000004 ≠ 0.3.'),

    (TF, H, 'set trong Python là một tập hợp có thứ tự (ordered).',
     tf(False), 'set KHÔNG đảm bảo thứ tự các phần tử.'),

    (TF, H, 'Một hàm trong Python có thể gọi lại chính nó (đệ quy).',
     tf(True), 'Python hỗ trợ đệ quy (recursion).'),

    (TF, ME, 'Biến toàn cục (global) có thể được đọc bên trong hàm mà không cần khai báo global.',
     tf(True), 'Đọc thì được; muốn GÁN lại biến global trong hàm mới cần từ khóa global.'),
]


class Command(BaseCommand):
    help = 'Tạo 100 câu trắc nghiệm Python mẫu vào ngân hàng câu hỏi'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true',
                            help='Xóa toàn bộ câu hỏi cũ của môn Python trước khi thêm')

    def handle(self, *args, **options):
        # Người tạo: ưu tiên teacher, sau đó admin/superuser
        author = (User.objects.filter(role='teacher').first()
                  or User.objects.filter(is_superuser=True).first()
                  or User.objects.first())
        if not author:
            self.stderr.write('Chua co tai khoan nao. Hay tao superuser truoc.')
            return

        subject, _ = Subject.objects.get_or_create(
            name=SUBJECT_NAME,
            defaults={'code': SUBJECT_CODE, 'created_by': author},
        )
        topic, _ = Topic.objects.get_or_create(subject=subject, name='Tong hop Python')

        if options['reset']:
            deleted = Question.objects.filter(subject=subject).delete()
            self.stdout.write(self.style.WARNING(f'Da xoa cau hoi cu: {deleted}'))

        created = 0
        skipped = 0
        for q_type, difficulty, content, choices, explanation in QUESTIONS:
            # Tránh trùng lặp theo nội dung trong cùng môn
            if Question.objects.filter(subject=subject, content=content).exists():
                skipped += 1
                continue

            question = Question.objects.create(
                subject=subject,
                topic=topic,
                question_type=q_type,
                difficulty=difficulty,
                content=content,
                explanation=explanation,
                points=1.0,
                created_by=author,
            )
            for i, (label, ctext, is_correct) in enumerate(choices, 1):
                Choice.objects.create(
                    question=question, label=label, content=ctext,
                    is_correct=is_correct, order=i,
                )
            created += 1

        total = Question.objects.filter(subject=subject).count()
        self.stdout.write(self.style.SUCCESS(
            f'Hoan tat! Tao moi: {created} cau | Bo qua (trung): {skipped} | '
            f'Tong cau hoi mon {SUBJECT_CODE}: {total}'
        ))
