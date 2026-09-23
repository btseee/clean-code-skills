package com.example.bank.service;

import com.example.bank.entity.Account;
import com.example.bank.repository.AccountRepository;
import org.springframework.stereotype.Service;

@Service
public class AccountService {

    private final AccountRepository accountRepository;

    public AccountService(AccountRepository accountRepository) {
        this.accountRepository = accountRepository;
    }

    public Account deposit(Long accountId, long amountCents) {
        Account account = find(accountId);
        account.deposit(amountCents);
        return accountRepository.save(account);
    }

    public Account withdraw(Long accountId, long amountCents) {
        Account account = find(accountId);
        account.withdraw(amountCents);
        return accountRepository.save(account);
    }

    private Account find(Long accountId) {
        return accountRepository.findById(accountId)
                .orElseThrow(() -> new IllegalArgumentException("no such account: " + accountId));
    }
}
