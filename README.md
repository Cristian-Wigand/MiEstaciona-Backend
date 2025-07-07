# MiEstaciona v1 – Backend

Este proyecto corresponde al **backend** de MiEstaciona v1, desarrollado en Python utilizando Flask. Se encarga de la gestión de usuarios, autenticación, registros de vehículos, cálculos de tarifas y generación de datos estadísticos.

## 🌐 Cómo usar

El backend está conectado al frontend desplegado en Vercel. Para probarlo:

1. Ingresa a la aplicación en:
   ➡️ [https://mi-estacionav1.vercel.app](https://mi-estacionav1.vercel.app)

2. Utiliza las siguientes credenciales de prueba para iniciar sesión según el rol que quieras probar.

## 🔑 Credenciales de prueba

### Usuario común
- **Correo:** juan@example.com
- **Contraseña:** 1234

### Trabajador
- **Correo:** ana@example.com
- **Contraseña:** abcd

### Administrador
- **Correo:** admin@gmail.com
- **Contraseña:** 123

## ⚙️ Funcionalidades disponibles

Dependiendo del rol, podrás probar:

✅ Registro e inicio de sesión con autenticación JWT.  
✅ Consulta de plazas disponibles y estado del estacionamiento.  
✅ Registro de vehículos y cálculo de tarifas.  
✅ Acceso a gráficos y estadísticas (solo admin).  
✅ Gestión de usuarios y trabajadores (solo admin).

## 🛠️ Tecnologías usadas

- Python
- Flask
- Flask-JWT-Extended
- Flask-SQLAlchemy
- PostgreSQL (en producción)
- Flask-CORS
