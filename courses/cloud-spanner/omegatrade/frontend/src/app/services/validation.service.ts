import { FormGroup } from '@angular/forms';
export class ValidationService {
    static getValidatorErrorMessage(validatorName: string, validatorValue?: any): object {
      const config = {
        required: 'Required',
        invalidEmailAddress: 'Invalid email address',
        invalidPassword: 'Invalid password. Password must be at least 6 characters long, and contain a number.',
        passwordNotMatch: 'Password and confirm password fields not matched.',
        minlength: `Minimum length ${validatorValue.requiredLength}`,
        maxlength: `Maximum length ${validatorValue.requiredLength}`
      };
      return config[validatorName];
    }
  
    static emailValidator(control): any {
      // RFC 2822 compliant regex
      if (control.value.match(/[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?/)) {
        return null;
      } else {
        return { invalidEmailAddress: true };
      }
    }
  
    static passwordValidator(control): any {
      if (control.value.match(/^(?=.*[0-9])[a-zA-Z0-9!@#$%^&*]{6,100}$/)) {
        return null;
      } else {
        return { invalidPassword: true };
      }
    }

    static checkPasswords(group: FormGroup) { 
      let password = group.controls.password.value;
      let confirmPassword = group.controls.confirmPassword.value;
      if(password && confirmPassword)
        return password === confirmPassword ? null : { passwordNotMatch : true };
      return null;  
    }
  }
  