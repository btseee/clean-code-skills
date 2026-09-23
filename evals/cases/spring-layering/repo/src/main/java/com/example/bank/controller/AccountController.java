package com.example.bank.controller;

import com.example.bank.entity.Account;
import com.example.bank.service.AccountService;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class AccountController {

    private final AccountService accountService;

    public AccountController(AccountService accountService) {
        this.accountService = accountService;
    }

    @PostMapping("/accounts/{id}/deposit")
    public Account deposit(@PathVariable Long id, @RequestParam long amountCents) {
        return accountService.deposit(id, amountCents);
    }

    @PostMapping("/accounts/{id}/withdraw")
    public Account withdraw(@PathVariable Long id, @RequestParam long amountCents) {
        return accountService.withdraw(id, amountCents);
    }
}
