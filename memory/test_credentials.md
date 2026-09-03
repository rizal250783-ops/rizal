# AO-360 Test Credentials

Base URL (backend): `${REACT_APP_BACKEND_URL}/api`

## Admin
- Email: `admin@hajimiskin.co.id`
- Password: `Admin12345`
- Role: admin (Full Access)

## Direktur (Read Only)
- Email: `hendri.kamal@hajimiskin.co.id`
- Password: `Direktur123`
- Role: direktur

## AO Lending (password: `Password123`)
- rizky.lending@hajimiskin.co.id
- dewi.lending@hajimiskin.co.id
- fajar.lending@hajimiskin.co.id
- siti.lending@hajimiskin.co.id

## AO Funding (password: `Password123`)
- budi.funding@hajimiskin.co.id
- maya.funding@hajimiskin.co.id
- andi.funding@hajimiskin.co.id
- lestari.funding@hajimiskin.co.id

## PIC Remedial (password: `Password123`)
- hendra.remedial@hajimiskin.co.id
- ratna.remedial@hajimiskin.co.id

## Auth endpoints
- POST /api/auth/login {email, password}
- POST /api/auth/logout
- GET  /api/auth/me
- POST /api/auth/change-password {current_password, new_password}

Security: account lockout after 5 failed logins (15 min), password policy min 8 chars letters+numbers, admin reset generates temp password + force change on next login.
