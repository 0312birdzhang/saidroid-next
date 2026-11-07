/* DumpMembers —— 用反射列出某个框架类的成员。
 * 用途：native 注册失败时报 "Unable to find static method xxx"，
 * 先确认目标类里到底有没有这个方法、签名是什么。
 * 用法：dalvikvm -cp ap.dex DumpMembers android.os.Binder
 */
import java.lang.reflect.Constructor;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;

public class DumpMembers {
    public static void main(String[] argv) throws Exception {
        String name = argv.length > 0 ? argv[0] : "android.os.Binder";
        String filter = argv.length > 1 ? argv[1] : null;
        Class<?> c = Class.forName(name);
        System.out.println("CLASS " + c.getName() + "  super=" + c.getSuperclass());
        for (Constructor<?> k : c.getDeclaredConstructors()) {
            if (filter != null && !k.toString().contains(filter)) continue;
            System.out.println("C " + k);
        }
        for (Method m : c.getDeclaredMethods()) {
            if (filter != null && !m.getName().contains(filter)) continue;
            System.out.println("M " + Modifier.toString(m.getModifiers()) + " " + m.getName()
                    + " " + types(m.getParameterTypes()) + " -> " + m.getReturnType().getName());
        }
        if (filter == null) {
            for (Field f : c.getDeclaredFields()) {
                System.out.println("F " + f.getType().getName() + " " + f.getName());
            }
        }
        System.out.flush();
    }

    static String types(Class<?>[] ts) {
        StringBuilder b = new StringBuilder("(");
        for (int i = 0; i < ts.length; i++) {
            if (i > 0) b.append(", ");
            b.append(ts[i].getName());
        }
        return b.append(")").toString();
    }
}
